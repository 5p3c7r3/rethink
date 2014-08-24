""" Model and Property classes. Borrowed heavily from google/appengine/ext/ndb/model

"""
import math
import types

from json import dumps

from datetime import tzinfo, timedelta, date

from . import utils

# set all the imports here from rethinkdb.* with "object" import removed
from rethinkdb.net import connect, Connection, Cursor
from rethinkdb.query import js, http, json, args, error, random, do, row, table, db, db_create, db_drop, db_list, table_create, table_drop, table_list, branch, asc, desc, eq, ne, le, ge, lt, gt, any, all, add, sub, mul, div, mod, type_of, info, time, monday, tuesday, wednesday, thursday, friday, saturday, sunday, january, february, march, april, may, june, july, august, september, october, november, december, iso8601, epoch_time, now, literal, make_timezone, and_, or_, not_
from rethinkdb.errors import RqlError, RqlClientError, RqlCompileError, RqlRuntimeError, RqlDriverError
from rethinkdb.ast import expr, RqlQuery
import rethinkdb.docs


def negative_field_check(should_check, value):
    if not should_check:
        return value

    if not isinstance(value, (int, float, long)):
        raise ValueError('%s field is the wrong type. Checked: int, long, float' % value)

    if not value < 0:
        raise ValueError('%s field is not a negative value' % value)


def positive_field_check(should_check, value):
    if not should_check:
        return value

    if not isinstance(value, (int, float, long)):
        raise ValueError('%s field is the wrong type. Checked: int, long, float' % value)

    if not value > 0:
        raise ValueError('%s field is not a positive value.' % value)


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
        if self._validator is not None:
            new_value = self._validator(self, value)
            if new_value is not None:
                value = new_value
        return value

    def to_db(self, entity):
        """ Transform the python value for storage in the db
        :param value: The value from python object
        :return: The value for the database
        """
        return self._do_validate(entity._values.get(self._name, self._default))

    def ensure_max_digits(self, value):
        if not self.max_digits:
            self.max_digits = int(self.max_digits)
            if self.max_digits > 0 and not value < math.pow(10, self.max_digits) and \
                    not value > -math.pow(10, self.max_digits):
                raise ValueError('%s field size invalid. Constraint: maximum %d digits. Value: %d' % (self._name, self.max_digits, value))
        return value

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


# todo make StringProperty default to indexed
# todo make TextProperty default to non-indexed


class TextProperty(Property):
    _max_length = None

    def _validate(self, value):
        if not isinstance(value, types.StringTypes):
            raise ValueError("String type expected; found %r" % (value,))

        if self._max_length and len(value) > self._max_length:
            raise ValueError("Value must be less than or equal to %s characters" % self._max_length)

        return value


class StringProperty(TextProperty):
    _max_length = 500


class IntegerProperty(Property):

    def _validate(self, value):
        if not isinstance(value, (int, long)):
            raise ValueError('Expected integer, got %r' % (value,))
        return int(value)


class FloatProperty(Property):

    def _validate(self, value):
        if not isinstance(value, (int, long, float)):
            raise ValueError('Expected float, got %r' % (value,))
        return float(value)


class TZ(tzinfo):
    def utcoffset(self, dt): return timedelta(minutes=-399)


class DateTimeProperty(Property):
    _auto_now_add = False
    _auto_now = False

    def __init__(self, required=False, default=None, auto_now=False, auto_now_add=False):
        self._auto_now = auto_now
        self._auto_now_add = auto_now_add

        super(DateTimeProperty, self).__init__(required=required, default=default)

    def validate(self, value):
        # datetime(2002, 12, 25, tzinfo=TZ()).isoformat(' ')
        # r.table("user").get("John").update({birth: r.ISO8601('1986-11-03T08:30:00-07:00')}).run(conn, callback)
        if not isinstance(value, date):
            raise TypeError("Must be a python datetime value")
        return value

    def to_db(self, entity):
        value = entity._values.get(self._name, self._default)
        if not value and self._auto_now or self._auto_now_add:
            return now()

        elif value and self._auto_now:
            return now()

        # todo all dates should be converted to UTC

        return iso8601(value.isoformat('T'))


class ObjectProperty(Property):
    def validate(self, value):
        if type(value) is not dict and type(value) is not list:
            raise ValueError('%s field is not dict or list type. Found type: %s' % (
                self._name,
                type(value))
            )

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
        the table name by setting _table on the class
        """
        if cls.__name__ == 'Model':
            return  # skip call on this class

        tables = table_list().run()
        if not cls._table_name() in tables:
            table_create(cls._table_name()).run()

    def _set_attributes(self, kwargs):
        cls = self.__class__
        for name, value in kwargs.iteritems():
            prop = getattr(cls, name)  # Raises AttributeError for unknown properties.
            if not isinstance(prop, Property):
                raise TypeError("Attempted to set non-property type; %s" % name)
            setattr(self, name, value)

    def __json__(self):
        d = {}
        for key in dir(self):
            if not key.startswith('_') and not hasattr(getattr(self, key), '__call__'):
                d[key] = getattr(self, key)
        return d

    def evaluate_insert(self, result):
        if 'errors' in result and result['errors'] > 1:
            raise IOError(dumps(result))
        elif result['inserted'] == 1.0:
            self.id = result.get('generated_keys', [self.id])[0]
        return result

    @classmethod
    def evaluate_update(cls, result):
        if 'updated' in result and result['updated'] == 0:
            raise ValueError(dumps(result))
        if 'replaced' in result and result['replaced'] == 0:
            raise ValueError(dumps(result))
        if 'errors' in result and result['errors'] > 0:
            raise IOError(dumps(result))
        return result

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
            attr = cls._meta[name]
            setattr(entity, attr._attr_name, value)
        return entity

    def _to_db(self):
        db_doc = {}

        # Validate any defined fields and set any defaults
        for name, attr in self._meta.iteritems():
            db_doc[name] = attr.to_db(self)

        if self.id:
            db_doc['id'] = self.id

        return db_doc

    def put(self):
        """ Serialize this document to JSON and put it in the database
        """
        return self.evaluate_insert(table(self._table_name()).insert(
            self._to_db(),
            upsert=True
        ).run(self._connection))
