from setuptools import setup

setup(
  name="rethink-rdb",
  version="1",
  description="An object mapper interface for rethinkdb",
  url="https://github.com/caoimhghin/rethink",
  maintainer="coimhghin",
  packages=['rdb'],
  install_requires=['rethinkdb', 'pytz']
)