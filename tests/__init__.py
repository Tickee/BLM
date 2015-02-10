from sqlalchemy.engine import create_engine
import sqlahelper
import unittest

Session = sqlahelper.get_session()
Base = sqlahelper.get_base()

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        engine = create_engine('sqlite:///:memory:', echo=True)
        Session.configure(bind=engine)
        metadata = Base.metadata
        metadata.create_all(engine)

    def tearDown(self):
        Session.remove()