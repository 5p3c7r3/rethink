import unittest
import rdb

from datetime import datetime
from dateutil.tz import tzutc

from nose.tools import *

rdb.connect(host='localhost', port=28015, db='rethink').repl()
try:
    rdb.db_drop('rethink').run()
except Exception:
    pass
rdb.db_create('rethink').run()


class TestModel(rdb.Model):
    name = rdb.StringProperty()


class TestDateTimeModel(rdb.Model):
    name = rdb.StringProperty()
    created = rdb.DateTimeProperty()


class TestDateTimeAutoNow(rdb.Model):
    name = rdb.StringProperty()
    created = rdb.DateTimeProperty(auto_now=True)


class TestModelStringProperty(rdb.Model):
    name = rdb.StringProperty("n", required=False, default="__default__", validator=lambda p, val: str(val).upper())


class TestModelBooleanProperty(rdb.Model):
    lovable = rdb.BooleanProperty()


class TestValidatorMRO(rdb.Model):
    children = rdb.PositiveIntegerProperty()


class TestFloatProperty(rdb.Model):
    dollars = rdb.FloatProperty(default=1.0)


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
        test_model = TestDateTimeModel(name='Jack', created=datetime(2002, 12, 25, tzinfo=tzutc()))
        test_model.put()

    def test_datetime_auto_now(self):
        test_model = TestDateTimeAutoNow(name='Jack')
        test_model.put()

        result = TestDateTimeAutoNow.get_by_id(test_model.id)
        self.assertTrue(result.created)

        self.assertLess(result.created, datetime.now(tzutc()))

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

    @raises(ValueError)
    def test_invalid_validator(self):
        class TestModelStringProperty(rdb.Model):
            name = rdb.StringProperty(validator="not a function")

if __name__ == '__main__':
    unittest.main()