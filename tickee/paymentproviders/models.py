from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, String
from tickee.core.db.types import MutationDict, JSONEncodedDict
import sqlahelper
import sqlalchemy.orm as orm

Base = sqlahelper.get_base()
Session = sqlahelper.get_session()

class PaymentProviderInformation(Base):
    
    # Meta
    
    __tablename__ = 'tickee_payment_provider_info'
    
    # Columns
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('tickee_accounts.id'))
    provider_info = Column(MutationDict.as_mutable(JSONEncodedDict))
    provider_type = Column(String)
    
    # Relations
    
    account = orm.relationship("Account", backref=orm.backref("paymentproviders"))
    
    def __init__(self):
        self.provider_info = {}
    
    def get_info(self, key):
        return self.provider_info.get(key)
    

class MonthlyTransactions(Base):
    
    # Meta
    
    __tablename__ = 'tickee_monthly_transactions'
    
    # Columns
    
    month = Column(Integer, primary_key=True)
    year = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('tickee_accounts.id'), primary_key=True)
    amount = Column(Integer)
    
    # Relations
    
    account = orm.relationship('Account', backref=orm.backref('monthly_transactions', lazy='dynamic'))
    
    # Constructor
    
    def __init__(self, account_id, year, month):
        self.account_id = account_id
        self.year = year
        self.month = month
        self.amount = 0