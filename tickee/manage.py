import importlib
import logging
import logging.config
import sqlahelper
import sqlalchemy
try:
    import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

tlogger = logging.getLogger('technical')

def load_database(database=settings.DATABASE):
    engine = sqlalchemy.engine_from_config(database, prefix='')
    sqlahelper.add_engine(engine)
    tlogger.info("database set up: %s" % engine)
    for package in settings.INSTALLED_APPS:
        try:
            importlib.import_module(package + ".models")
        except ImportError:
            result = "failed"
        else:
            result = "done"
        finally:
            tlogger.debug("loading models: %s.models.. %s" % (package, result))
    Base = sqlahelper.get_base()
    tlogger.info('creating database tables')
    Base.metadata.create_all(engine)        


def reload_logging(ini_file='./logging.ini'):
    logging.config.fileConfig(ini_file)    

if __name__ == "__main__":
    reload_logging()
    load_database()