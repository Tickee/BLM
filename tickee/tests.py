from tickee.manage import reload_logging, load_database
import celeryconfig
import sqlahelper
import transaction
import unittest

celeryconfig.CELERY_ALWAYS_EAGER = True
print "CELERY_ALWAYS_EAGER activated."

class BaseTestCase(unittest.TestCase):
    
    def setUp(self):
        reload_logging('./logging.ini') 
        load_database({'url':'sqlite:///:memory:'})
        sqlahelper.get_session().configure(extension=[])
        transaction.begin()

    def tearDown(self):
        Session = sqlahelper.get_session()
        Session.remove()