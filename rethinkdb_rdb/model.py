""" Model and Property classes. Borrowed heavily from google/appengine/ext/ndb/model
"""
import re
import types
import pytz
from json import dumps

from datetime import date, datetime

from . import utils

# set all the imports here from rethinkdb.* with "object" import removed
from rethinkdb.net import connect, Connection, Cursor
from rethinkdb.query import js, http, json, args, error, random, do, row, table, db, db_create, db_drop, db_list, table_create, table_drop, table_list, branch, asc, desc, eq, ne, le, ge, lt, gt, any, all, add, sub, mul, div, mod, type_of, info, time, monday, tuesday, wednesday, thursday, friday, saturday, sunday, january, february, march, april, may, june, july, august, september, october, november, december, iso8601, epoch_time, now, literal, make_timezone, and_, or_, not_
from rethinkdb.errors import RqlError, RqlClientError, RqlCompileError, RqlRuntimeError, RqlDriverError
from rethinkdb.ast import expr, RqlQuery
import rethinkdb.docs


class Property(object):

    _attr_name = None
    _name = None
    _required = True
    _default = None
    _validator = None
    _indexed = True
    _positional = 1

    @utils.positional(1 + _positional)  # Add 1 for self.
    def __init__(self, name=None, indexed=None, required=False, default=None, validator=None):
        if name is not None:
            if isinstance(name, unicode):
                name = name.encode('utf-8')
            if not isinstance(name, str):
                raise TypeError('Name %r is not a string' % (name,))
            if '.' in name:
                raise ValueError('Name %r cannot contain period characters' % (name,))
            self._name = name

        if indexed is not None:
            self._indexed = indexed

        if default is not None:
            self._default = default

        if required is not None:
            self._required = required

        if validator is not None:
            if not hasattr(validator, '__call__'):
                raise TypeError("Validator must be callable or None; received %r" % validator)
            self._validator = validator

    def _set_name(self, name):
        """ Assign a name if no name was given. The name of the class attribute is
        passed in from _map_properties as a default name. This allows assignment of a
        shorter name for database storage, but still use a verbose name in code.
        """
        self._attr_name = name
        if self._name is None:
            self._name = name

    def _do_validate(self, value):
        value = self._call_validation(value)
        if self._validator is not None:
            new_value = self._validator(self, value)
            if new_value is not None:
                value = new_value
        return value

    def _call_validation(self, value):
        """ Call the initial set of _validate() methods using reverse Method Resolution Order.
        For instance if class hierarchy looks like (-> = extends):

        A -> B -> C -> D

        This will start with the most base-class validate method and execute backwards:

        D.validate()
        C.validate()
        B.validate()
        A.validate()
        """
        if value is None:
            if self._required:
                raise ValueError("No value given for required property: %s" % self._attr_name)
            else:
                return value

        validate_methods = self._find_methods('_validate')
        validate_methods.reverse()
        call = self._apply_list(validate_methods)
        return call(value)

    @classmethod
    def _find_methods(cls, *names):
        """ Compute a list of composable methods.

        Because this is a common operation and the class hierarchy is
        static, the outcome is cached (assuming that for a particular list
        of names the reversed flag is either always on, or always off).

        Args:
            *names: One or more method names.

        Returns:
            A list of callable class method objects.
        """
        cache = cls.__dict__.get('_find_methods_cache')
        if cache:
            hit = cache.get(names)
            if hit is not None:
                return hit
        else:
            cls._find_methods_cache = cache = {}
        methods = []
        for c in cls.__mro__:
            for name in names:
                method = c.__dict__.get(name)
                if method is not None:
                    methods.append(method)
        cache[names] = methods
        return methods

    def _apply_list(self, methods):
        """ Return a single callable that applies a list of methods to a value.

        If a method returns None, the last value is kept; if it returns
        some other value, that replaces the last value.  Exceptions are
        not caught.
        """
        def call(value):
            for method in methods:
                newvalue = method(self, value)
                if newvalue is not None:
                    value = newvalue
            return value
        return call

    def _do_to_db(self, entity):
        """ Transform the python value for storage in the db, first running all
        validators on the property.
        """
        value = self._do_validate(entity._values.get(self._name, self._default))
        if hasattr(self, '_to_db'):
            value = self._to_db(value)
        return value

    def _do_from_db(self, entity, value):
        """ Set the property value from the db and transform it for python
        """
        if hasattr(self, '_from_db'):
            value = self._from_db(value)
        entity._values[self._name] = value

    def __get__(self, entity, unused_cls=None):
        """Descriptor protocol: get the value from the entity."""
        if entity is None:
            return self  # __get__ called on class
        return entity._values.get(self._name, self._default)

    def __set__(self, entity, value):
        """Descriptor protocol: set the value on the entity."""
        entity._values[self._name] = self._do_validate(value)

    def __delete__(self, entity):
        """Descriptor protocol: delete the value from the entity."""
        if self._name in entity._values:
            del entity._values[self._name]


class BooleanProperty(Property):
    """ A Property whose value is a Python bool. Integers are converted into booleans
    by changing 0 to False and anything else to True
    """

    def _validate(self, value):
        if isinstance(value, int):
            if value == 0:
                value = False
            else:
                value = True

        if not isinstance(value, bool):
            raise ValueError('Expected bool, got %r' % (value,))

        return value


class TextProperty(Property):
    _max_length = None
    _indexed = False

    def _validate(self, value):
        if not isinstance(value, types.StringTypes):
            raise ValueError("String type expected; found %r" % (value,))

        if self._max_length and len(value) > self._max_length:
            raise ValueError("Value must be less than or equal to %s characters" % self._max_length)

        return value


class StringProperty(TextProperty):
    _max_length = 500
    _indexed = True


class IntegerProperty(Property):

    def _validate(self, value):
        if not isinstance(value, (int, long)):
            raise ValueError('Expected integer, got %r' % (value,))
        return int(value)


class PositiveIntegerProperty(IntegerProperty):

    def _validate(self, value):
        if int(value) < 0:
            raise ValueError('Expected positive integer, got %r' % (value,))
        return value


class FloatProperty(Property):

    def _validate(self, value):
        if not isinstance(value, (int, long, float)):
            raise ValueError('Expected float, got %r' % (value,))
        return float(value)


class DateTimeProperty(Property):
    _auto_now_add = False
    _auto_now = False

    @utils.positional(1 + Property._positional)  # Add 1 for self.
    def __init__(self, name=None, indexed=None, required=False, default=None, validator=None, auto_now=False, auto_now_add=False):
        self._auto_now = auto_now
        self._auto_now_add = auto_now_add

        super(DateTimeProperty, self).__init__(required=required, default=default)

    def _validate(self, value):
        if not isinstance(value, date):
            raise TypeError("Must be a python datetime value")
        return value

    def _from_db(self, value):
        return value

    def _to_db(self, value):
        if value is None and self._auto_now or self._auto_now_add:
            return now()

        elif self._auto_now:
            return now()

        if value is None and not self._required:
            return None

        if value.tzinfo:
            value = value.astimezone(pytz.utc)
        else:
            value = pytz.utc.localize(value)

        return value


class ObjectProperty(Property):

    def _validate(self, value):
        if type(value) is not dict and type(value) is not list:
            raise ValueError('Expected list or dict type. Found %r' % (value,))

        return value


class MetaModel(type):

    def __init__(cls, name, bases, classdict):
        """ Initialize the class, map properties and create the
        database table.
        """
        super(MetaModel, cls).__init__(name, bases, classdict)
        cls._map_properties()
        cls._sync_table()


class Model(object):

    __metaclass__ = MetaModel

    id = None

    _limit = 0
    _order_by = None
    _meta = None
    _values = None
    _connection = None
    _non_atomic = True

    def __init__(self, **kwargs):
        if 'id' in kwargs:
            self.id = kwargs.pop('id')

        self._values = {}
        self._set_attributes(kwargs)

    @classmethod
    def _map_properties(cls):
        """ Map all the properties on the class that will make up the data that
        we store. This defines the schema for this table. Extra properties can
        be set, but they won't be saved unless they extend Property
        """
        cls._meta = {}
        for name in set(dir(cls)):
            if name.startswith('_'):
                continue
            attr = getattr(cls, name, None)
            if isinstance(attr, Property):
                attr._set_name(name)
                cls._meta[attr._name] = attr

    @classmethod
    def _table_name(cls):
        return getattr(cls, '_table', cls.__name__)

    @classmethod
    def _sync_table(cls):
        """ Create a table for this model if it doesn't already exist, override
        the table name by setting _table on the class. Updates simple indexes as
        defined by the properties.

        Complex indexes need to be created separately.
        """
        if cls.__name__ == 'Model':
            return  # skip call on this class

        tables = table_list().run()
        if not cls._table_name() in tables:
            table_create(cls._table_name()).run()

        indexes = table(cls._table_name()).index_list().run()
        for name, attr in cls._meta.iteritems():
            if attr._indexed and attr._name not in indexes:
                table(cls._table_name()).index_create(attr._name).run(noreply=True)
            elif not attr._indexed and attr._name in indexes:
                table(cls._table_name()).index_drop(attr._name).run(noreply=True)

    def _set_attributes(self, kwargs):
        cls = self.__class__
        for name, value in kwargs.iteritems():
            prop = getattr(cls, name)  # Raises AttributeError for unknown properties.
            if not isinstance(prop, Property):
                raise TypeError("Attempted to set non-property type; %s" % name)
            setattr(self, name, value)

    @classmethod
    def query(cls):
        """ The rethinkdb query object. Exposes RQL queries for this table
        """
        rq = table(cls._table_name())
        if cls._order_by:
            rq = rq.order_by(*tuple(
                [order if not order[:1] == '-' else desc(order[1:]) for order in list(cls._order_by)]
            ))
        if cls._limit:
            rq = rq.limit(int(cls._limit))
        return rq

    @classmethod
    def all(cls, connection=None):
        return [cls(**row) for row in cls.query().run(connection)]

    @classmethod
    def get_by_id(cls, id, connection=None):
        if not id:
            return None

        result = cls.query().get(id).run(connection)
        if result:
            result = cls._from_db(result)
        return result

    @classmethod
    def delete(cls, id, connection=None):
        if not id:
            return None
        return cls.query().get(id).delete().run(connection)

    @classmethod
    def _from_db(cls, db_dict):
        entity = cls()
        entity.id = db_dict.pop('id')
        for name, value in db_dict.iteritems():
            attr = cls._meta.get(name)
            if not attr:
                # maybe it was removed during class refactor, or
                # added via some other means.
                attr = ObjectProperty()
                cls._meta[name] = attr
            attr._do_from_db(entity, value)
        return entity

    def to_dict(self):
        _doc = {}
        for name, attr in self._meta.iteritems():
            _doc[attr._attr_name] = getattr(self, attr._attr_name)

        if self.id:
            _doc['id'] = self.id

        return _doc

    def _to_db(self):
        db_doc = {}

        # Validate any defined fields and set any defaults
        for name, attr in self._meta.iteritems():
            db_doc[name] = attr._do_to_db(self)

        if self.id:
            db_doc['id'] = self.id

        return db_doc

    def put(self):
        """ Serialize this document to JSON and put it in the database
        """
        result = table(self._table_name()).insert(self._to_db(), conflict="update").run(self._connection)
        if 'errors' in result and result['errors'] > 0:
            raise IOError(dumps(result))
        elif result['inserted'] == 1.0:
            self.id = result.get('generated_keys', [self.id])[0]
        return result