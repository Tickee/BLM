'''
Created on Jun 9, 2011

@author: Kevin Van Wilder <kevin@tick.ee>
'''

from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String, DateTime
from tickee.core.db.types import JSONEncodedDict
import datetime
import sqlahelper


Base = sqlahelper.get_base()

class CrmDump(Base):
    """
    """
    
    __tablename__ = 'tickee_crmdump'
    
    # Columns
    
    id = Column(Integer, primary_key=True, index=True)
    logged_at = Column(DateTime)
    object_name = Column(String)
    object_id = Column(Integer)
    json = Column(JSONEncodedDict)
    
    def __init__(self, name, object_id, dict_object):
        self.object_name = name
        self.object_id = object_id
        self.logged_at = datetime.datetime.utcnow()
        self.json = dict_object