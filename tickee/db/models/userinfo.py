from sqlalchemy.schema import ForeignKey, Column
from sqlalchemy.types import Integer, String
from tickee.core.db.types import JSONEncodedDict
from tickee.db.models import user
import sqlahelper
import sqlalchemy.orm as orm


Base = sqlahelper.get_base()

class UserInfo(Base):
    
    __tablename__ = "tickee_userinfo"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('tickee_users.id'))
    info_type = Column(String)
    json = Column(JSONEncodedDict)
    
    user = orm.relationship('User', backref=orm.backref('userinfo', order_by=id))
    
    def __init__(self, user_id, info_type, info):
        self.user_id = user_id
        self.info_type = info_type
        self.info = info