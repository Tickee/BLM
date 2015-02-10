from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String, Text
import sqlahelper

Base = sqlahelper.get_base()
Session = sqlahelper.get_session()

class TextLocalisation(Base):
    
    __tablename__ = "tickee_localisation"
    
    # Columns
    
    id = Column(Integer, primary_key=True)
    reference_id = Column(Integer, index=True)
    lang = Column(String(5))
    text = Column(Text)
    
    # Constructor
    
    def __init__(self, text, lang="en", ref_id=None):
        self.reference_id = ref_id
        self.text = text
        self.lang = lang
        
    # Representation
    
    def __repr__(self):
        return "<TextLocalisation('%s','%s', '%s')>" % (self.reference_id, 
                                                        self.lang, self.text)