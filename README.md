## RethinkDB Object Mapper
[![Build Status](https://travis-ci.org/caoimhghin/rethink.svg?branch=master)](https://travis-ci.org/caoimhghin/rethink)
[![Coverage Status](https://coveralls.io/repos/caoimhghin/rethink/badge.png?branch=master)](https://coveralls.io/r/caoimhghin/rethink?branch=master)

### Inspired by
* Google Appengine NDB: https://developers.google.com/appengine/docs/python/ndb/
* RWrapper: https://github.com/dparlevliet/rwrapper
* RethinkEngine: https://github.com/bwind/rethinkengine
* PyRethinkORM: https://github.com/JoshAshby/pyRethinkORM

### Usage

#### Establish a connection
A connection manager would be nice to build, something that can be easily plugged into Django or Flask request
cycles and also pull connections from an available pool. For now do something like this:

<pre><code>rdb.connect(host='localhost', port=28015, db='rethink').repl()
try:
    rdb.db_drop('rethink').run()
except Exception:
    pass
rdb.db_create('rethink').run()
</code></pre>

#### Create your models
The models look a lot like Appengine NDB Models

<pre><code>class Contact(rdb.Model):
    first_name = rdb.StringProperty()
    last_name = rdb.StringProperty()
    created = rdb.DateTimeProperty()`
</code></pre>

#### Property types
The property types closely resemble NDB as well, currently working on implementing these with similar default
indexing behavior. Check the unit tests for examples.

#### Property Options
Most property types support some standard arguments. The first is an optional argument to specify the database name
for the property. This allows you to provide a shorter name to put in the database as an optimization while using a
more verbose name in your code.

The following additional keyword arguments are also supported

<table>
<th>
    <td>Argument</td>
    <td>Type</td>
    <td>Default</td>
    <td>Description</td>
</th>
<tr>
    <td>indexed</td>
    <td></td>
    <td></td>
    <td></td>
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

    All datetimes are stored in the database with timezone information in UTC time.

<table>
<th>
    <td>Option</td>
    <td>Description</td>
</th>
<tr>
    <td>auto_now_add</td>
    <td>Set property to current date/time when entity is created.</td>
</tr>
<tr>
    <td>auto_now</td>
    <td>Set property to current date/time when entity is created and whenever it is updated.</td>
</tr>
</table>





