from sqlalchemy.schema import Column
from sqlalchemy.types import String
import sqlahelper

Base = sqlahelper.get_base()

class Currency(Base):
    """
    A medium of exchange, e.g. "USD", "EUR", etc.
    """
    
    __tablename__ = 'tickee_currencies'
    
    # Columns
    name = Column(String, primary_key=True)
    full_name = Column(String)
        
    def __init__(self, iso_code, full_name):
        """
        Construct a new ``Currency`` object.
        """
        self.name = iso_code
        self.full_name = full_name