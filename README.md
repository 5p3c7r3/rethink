## RethinkDB Object Mapper
### Build status:
[![Build Status](https://travis-ci.org/caoimhghin/rethink.svg?branch=master)](https://travis-ci.org/caoimhghin/rethink)
[![Coverage Status](https://coveralls.io/repos/caoimhghin/rethink/badge.png?branch=master)](https://coveralls.io/r/caoimhghin/rethink?branch=master)
### Inspired by:
* Google Appengine NDB: https://developers.google.com/appengine/docs/python/ndb/
* RWrapper: https://github.com/dparlevliet/rwrapper
* RethinkEngine: https://github.com/bwind/rethinkengine
* PyRethinkORM: https://github.com/JoshAshby/pyRethinkORM
### Getting started
#### Establish a connection
A connection manager would be nice to build, something that can be easily plugged into Django or Flask request
cycles and also pull connections from an available pool. For now do something like this:
`rdb.connect(host='localhost', port=28015, db='rethink').repl()
try:
    rdb.db_drop('rethink').run()
except Exception:
    pass
rdb.db_create('rethink').run()`
#### Create your models
The models look a lot like Appengine NDB Models
`class Contact(rdb.Model):
    first_name = rdb.StringProperty()
    last_name = rdb.StringProperty()
    created = rdb.DateTimeProperty()`
#### Property types
The property types closely resemble NDB as well, currently working on implementing these with similar default
indexing behavior. Check the unit tests for examples.
