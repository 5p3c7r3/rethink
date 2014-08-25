from setuptools import setup

setup(
  name="rethinkdb_rdb",
  version="1",
  description="The object mapper interface for rethinkdb",
  url="https://github.com/caoimhghin/rethink",
  maintainer="coimhghin",
  packages=['rethinkdb_rdb'],
  install_requires=['rethinkdb', 'pytz']
)