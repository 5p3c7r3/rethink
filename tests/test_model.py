import pytz
import rethinkdb_rdb
import unittest

from datetime import datetime

from nose.tools import *

rethinkdb_rdb.connect(host='localhost', port=28015, db='rethink').repl()
try:
    rethinkdb_rdb.db_drop('rethink').run()
except Exception:
    pass
rethinkdb_rdb.db_create('rethink').run()


class TestModel(rethinkdb_rdb.Model):
    name = rethinkdb_rdb.StringProperty(indexed=False)


class TestDateTimeModel(rethinkdb_rdb.Model):
    name = rethinkdb_rdb.StringProperty()
    created = rethinkdb_rdb.DateTimeProperty(indexed=False)


class TestDateTimeAutoNow(rethinkdb_rdb.Model):
    name = rethinkdb_rdb.StringProperty()
    created = rethinkdb_rdb.DateTimeProperty(auto_now=True, indexed=False)


class TestModelStringProperty(rethinkdb_rdb.Model):
    name = rethinkdb_rdb.StringProperty("n", indexed=False, required=False, default="__default__", validator=lambda p, val: str(val).upper())


class TestModelBooleanProperty(rethinkdb_rdb.Model):
    lovable = rethinkdb_rdb.BooleanProperty(indexed=False)


class TestValidatorMRO(rethinkdb_rdb.Model):
    children = rethinkdb_rdb.PositiveIntegerProperty(indexed=False)


class TestFloatProperty(rethinkdb_rdb.Model):
    dollars = rethinkdb_rdb.FloatProperty(default=1.0, indexed=False)


class TestRequiredProperty(rethinkdb_rdb.Model):
    name = rethinkdb_rdb.StringProperty(required=True, indexed=False)
    found_on = rethinkdb_rdb.DateTimeProperty(required=True, indexed=False)


class TestModelFunctions(unittest.TestCase):

    def setUp(self):
        pass

    def test_create(self):
        """ Create, store and read a TestModel
        """
        test_model = TestModel(name='Jack')
        test_model.put()

        self.assertTrue(test_model.id)
        self.assertEqual(test_model.name, 'Jack')

    def test_update(self):
        """ Create and update a model, verify changes are saved
        """
        test_model = TestModel(name='Jack')
        test_model.put()
        id = test_model.id

        test_model = TestModel.get_by_id(id)
        test_model.name = 'Alice'
        test_model.put()

        self.assertEqual(id, test_model.id)
        self.assertEqual(test_model.name, 'Alice')

    def test_get(self):
        test_model = TestModel(name='Jack')
        test_model.put()

        result = TestModel.get_by_id(test_model.id)
        self.assertEqual(result.id, test_model.id)

    def test_delete(self):
        test_model = TestModel(name='Jack')
        test_model.put()

        id = test_model.id
        TestModel.delete(id)

        result = TestModel.get_by_id(id)
        self.assertFalse(result)

    def test_datetime(self):
        test_model = TestDateTimeModel(name='Jack', created=datetime(2002, 12, 25))
        test_model.put()

    def test_datetime_auto_now(self):
        test_model = TestDateTimeAutoNow(name='Jack')
        test_model.put()

        result = TestDateTimeAutoNow.get_by_id(test_model.id)
        self.assertTrue(result.created)

        self.assertLess(result.created, datetime.now(pytz.timezone('UTC')))

    def test_set_id(self):
        test_model = TestModel(id='jackwuzhere', name='Jack')
        test_model.put()

        self.assertEqual(test_model.id, 'jackwuzhere')

    def test_model_string_property(self):
        m = TestModelStringProperty(name="James Bond")
        m.put()
        self.assertEqual(m._to_db()['n'], 'JAMES BOND')
        self.assertEqual(m.name, "JAMES BOND")

        o = TestModelStringProperty.get_by_id(m.id)
        self.assertEqual(o._to_db()['n'], 'JAMES BOND')
        self.assertEqual(o.name, "JAMES BOND")

    @raises(ValueError)
    def test_model_string_property_maxlength(self):
        # by default a string can't be longer than 500 characters
        m = TestModelStringProperty(name="x"*501)
        m.put()

    @raises(ValueError)
    def test_model_invalid_string_property(self):
        m = TestModelStringProperty(name=12345)
        m.put()

    def test_model_boolean_property(self):
        m = TestModelBooleanProperty(lovable=True)
        m.put()
        m = TestModelBooleanProperty.get_by_id(m.id)
        self.assertTrue(m.lovable)

        m = TestModelBooleanProperty(lovable=0)
        m.put()
        self.assertFalse(m.lovable)

        m = TestModelBooleanProperty(lovable=1)
        m.put()
        self.assertTrue(m.lovable)


    @raises(ValueError)
    def test_model_invalid_boolean_property(self):
        m = TestModelBooleanProperty(lovable="false")
        m.put()

    def test_validate_mro(self):
        try:
            TestValidatorMRO(children="abcd")
        except ValueError as e:
            # this should be error expected integer from the base class IntegerProperty,
            # not the PositiveIntegerProperty validator
            self.assertTrue("Expected integer" in e.message)

    def test_float_property(self):
        m = TestFloatProperty()
        m.dollars = 12.5
        m.put()

        m = TestFloatProperty.get_by_id(m.id)
        self.assertEqual(m.dollars, 12.5)

        # integers are allowed
        m.dollars = 20
        m.put()

        m = TestFloatProperty.get_by_id(m.id)
        self.assertEqual(m.dollars, 20)

    @raises(ValueError)
    def test_invalid_float_property(self):
        TestFloatProperty(dollars="not a float")

    @raises(TypeError)
    def test_invalid_validator(self):
        class TestModelStringProperty(rethinkdb_rdb.Model):
            name = rethinkdb_rdb.StringProperty(validator="not a function")

    @raises(ValueError)
    def test_required_string_property(self):
        # missing required StringProperty
        m = TestRequiredProperty(found_on=datetime(2002, 12, 25))
        m.put()

    @raises(ValueError)
    def test_required_datetime_property(self):
        # missing required DateTimeProperty
        m = TestRequiredProperty(name="James Bond")
        m.put()

    def test_timezone_stored_as_utc(self):
        my_date = datetime(2014, 11, 11, 0, 0, 0, 0, pytz.timezone('US/Pacific'))
        test_model = TestDateTimeModel(name='Jack', created=my_date)
        test_model.put()

        m = TestDateTimeModel.get_by_id(test_model.id)
        self.assertEqual(m.created.isoformat(), my_date.astimezone(pytz.utc).isoformat())

    def test_index_creation(self):
        class TestIndexesModel(rethinkdb_rdb.Model):
            name = rethinkdb_rdb.StringProperty() # indexed by default
            a_very_long_verbose_name = rethinkdb_rdb.StringProperty(name='short')

        indexes = rethinkdb_rdb.table(TestIndexesModel._table_name()).index_list().run()
        self.assertTrue('name' in indexes)

        # should use the short codename of a property if provided
        self.assertTrue('short' in indexes)


if __name__ == '__main__':
    unittest.main()