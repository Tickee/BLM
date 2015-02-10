from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, DateTime
from tickee.core.db.types import JSONEncodedDict
import datetime
import sqlahelper
import sqlalchemy.orm as orm

Base = sqlahelper.get_base()

class TicketScan(Base):
    
    __tablename__ = "tickee_ticketscans"
    
    # Columns
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey('tickee_tickets.id'))
    scanned_date = Column(DateTime)
    extra_info = Column(JSONEncodedDict)
    
    # Relations
    
    ticket = orm.relationship('Ticket', backref="scans")
    
    # Constructor
    
    def __init__(self, 
                 scanned_date=datetime.datetime.utcnow(),
                 extra_info=dict()):
        self.scanned_date = scanned_date
        self.extra_info = extra_info