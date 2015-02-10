from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, String, DateTime
import datetime
import sqlahelper

Base = sqlahelper.get_base()


class Venue(Base):
    """
    A point of interest where a specific event will take place.
    """
    
    __tablename__ = 'tickee_venues'
    
    # Columns
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    latlng = Column(String)
    max_occupancy = Column(Integer)
    created_at = Column(DateTime)
    created_by = Column(Integer, ForeignKey('tickee_accounts.id'))
    
    # Relations
    
    creator = relationship('Account')
    address = relationship('Address', uselist=False, backref=backref("venue"))
    
    # Constructor
    
    def __init__(self, name):
        """
        Construct a new ``Venue`` object.
        """
        self.name = name
        self.created_at = datetime.datetime.utcnow()
        
        


class Address(Base):
    """
    Contains adress related information pertaining to a specific venue or other location.
    """
    
    __tablename__ = 'tickee_addresses'
    
    # Columns
    id = Column(Integer, primary_key=True, index=True)
    street_line1 = Column(String)
    street_line2 = Column(String)
    postal_code = Column(String, index=True)
    city = Column(String)
    country = Column(String)
    venue_id = Column(Integer, ForeignKey('tickee_venues.id'))
    
    def __init__(self, line1, line2, postal_code, city, country):
        """
        Construct a new ``Address`` object.
        """
        self.street_line1 = line1
        self.street_line2 = line2
        self.postal_code = postal_code
        self.city = city
        self.country = country