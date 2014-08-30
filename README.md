## RethinkDB Object Mapper Interface
[![Build Status](https://travis-ci.org/caoimhghin/rethink.svg?branch=master)](https://travis-ci.org/caoimhghin/rethink)
[![Coverage Status](https://coveralls.io/repos/caoimhghin/rethink/badge.png?branch=master)](https://coveralls.io/r/caoimhghin/rethink?branch=master)

### Inspired by
* Google Appengine NDB: https://developers.google.com/appengine/docs/python/ndb/
* RWrapper: https://github.com/dparlevliet/rwrapper
* RethinkEngine: https://github.com/bwind/rethinkengine
* PyRethinkORM: https://github.com/JoshAshby/pyRethinkORM

### Why
I consider NDB to be a premier programming interface in its simplicity and ease of use and understanding. I've worked
with NDB for a few years now and want to create a similarly beautiful and simple interface to a datastore that I can
host anywhere. RethinkDB seems to fit the datastore implementation that I'm looking for, so all we need is a
compelling interface that we will love to use and build products and services with.

#### Establish a connection
A connection manager would be nice to build, something that can be easily plugged into Django or Flask request
cycles and also pull connections from an available pool. For now do something like this:

<pre><code>import rethinkdb_rdb as rdb
rdb.connect(host='localhost', port=28015, db='rethink').repl()
rdb.db_create('rethink').run()
</code></pre>

#### Create your models
The models look a lot like Appengine NDB Models

<pre><code>class Contact(rdb.Model):
    first_name = rdb.StringProperty()
    last_name = rdb.StringProperty()
    created = rdb.DateTimeProperty()
</code></pre>

#### Property types
The property types closely resemble NDB as well, currently working on implementing these with similar default
indexing behavior. Check the unit tests for examples.
* `BooleanProperty`
* `StringProperty`
* `TextProperty`
* `IntegerProperty`
* `PositiveIntegerProperty`
* `FloatProperty`
* `DateTimeProperty`
* `ObjectProperty`

#### Property Options
Most property types support some standard arguments. The first is an optional argument to specify the database name
for the property. This allows you to provide a shorter name to put in the database as an optimization while using a
more verbose name in your code.

The following additional keyword arguments are also supported

<table>
<tr>
    <th>Argument</th>
    <th>Type</th>
    <th>Default</th>
    <th>Description</th>
</tr>
<tr>
    <td>indexed</td>
    <td>bool</td>
    <td>None</td>
    <td>Indicates whether this property should be indexed as a simple secondary rethinkdb index. If set to false after being created, the index will be removed.</td>
</tr>
<tr>
    <td>required</td>
    <td>bool</td>
    <td>False</td>
    <td>Property must have the value specified. Can be combined with default.</td>
</tr>
<tr>
    <td>default</td>
    <td>Property's underlying type</td>
    <td>None</td>
    <td>Default value of property if no value is specified.</td>
</tr>
<tr>
    <td>validator</td>
    <td>Function</td>
    <td>None</td>
    <td>Optional function to validate and possibly coerce the value. Should return value or raise an exception.</td>
</tr>
</table>

#### Date and Time Properties
There is only one property that maps to the python datetime class:
* `DateTimeProperty`

    All datetimes are stored in the database with timezone information in UTC time. Naive datetime will have UTC
    timezone appended to it. Depending on what you're doing this might be fine, or might mess things up for you, but
    rethinkdb requires timezone aware datetimes.

<table>
<tr>
    <th>Option</th>
    <th>Description</th>
</tr>
<tr>
    <td>auto_now_add</td>
    <td>Set property to current date/time when entity is created.</td>
</tr>
<tr>
    <td>auto_now</td>
    <td>Set property to current date/time when entity is created and whenever it is updated.</td>
</tr>
</table>


#### Next
Implement the next items
* `ComputedProperty`
* `repeated = True` attribute for Properties to make them stored as lists
* `get_multi` - along with the concept of a key which will hash ids with the class name


#### Example migrating queries from NDB

<pre><code>
# return cls.query(cls.subject == subject, cls.token == token).get()
result = cls.query().filter({'subject': subject, 'token': token}).run()
if result:
    return cls._from_db(list(result)[0])
return None
</code></pre>
