import unittest
import rdb

from datetime import datetime
from dateutil.tz import tzutc

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
        test_model.name = 'Alice'
        test_model.put()

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

if __name__ == '__main__':
    unittest.main()