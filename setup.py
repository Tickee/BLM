import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'SQLAlchemy', 'sqlahelper', 'psycopg2', # Database
    'requests', 'lxml', # Multisafepay
    'gchecky', # Google Checkout
    'jinja2', # email templating
    'celery', # concurrent task handling
    'simplejson',
    'gunicorn',
    'supervisor',
    ]

if sys.version_info[:3] < (2,5,0):
    requires.append('pysqlite')

setup(name='tickee',
      version='0.0',
      description='tick.ee business logic library',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        
        ],
      author='Kevin Van Wilder',
      author_email='kevin@tick.ee',
      url='http://tick.ee',
      keywords='ticket generation',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='tickee',
      install_requires = requires,
      )