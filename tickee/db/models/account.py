'''
Created on Jun 9, 2011

@author: Kevin Van Wilder <kevin@tick.ee>
'''

from pyramid_oauth2.models import OAuth2Client
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, String, Boolean
from tickee.core import l10n
from tickee.core.db.types import MutationDict, JSONEncodedDict
from tickee.exceptions import AccountError
import re
import sqlahelper
import sqlalchemy.orm as orm

Base = sqlahelper.get_base()

class Account(Base):
    """
    The general ``Account`` used to register organizers and visitors of events
    """
    
    __tablename__ = 'tickee_accounts'
    
    # Columns
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    full_name = Column(String)
    description_ref = Column(Integer)
    email = Column(String)
    active = Column(Boolean, default=False)
    website = Column(String)
    vat_percentage = Column(Integer)
    meta = Column(MutationDict.as_mutable(JSONEncodedDict))
    
    # Relations
    
    users = orm.relationship('UserAccountAssociation', backref=orm.backref("account"))
        
    # Connection to Pyramid_OAuth2
    
    client_id = Column(Integer, ForeignKey('oauth2_client.id'))
    client = orm.relationship(OAuth2Client, backref=orm.backref("account", uselist=False))
    
    def __init__(self, name, email):
        """
        Construct a new ``Account`` object.
        """
        p = re.compile('^[-\w]+$')
        if p.search(name) is None:
            raise AccountError("Shortname may only contain alphanumeric characters.")
        self.name = name.lower()
        self.email = email
        self.active = True
        self.description_ref = l10n.create_text_localisation().reference_id
        self.meta = {}
    
    # Description
    
    def set_description(self, text, lang='en'):
        """
        Sets the description for a specific language
        """
        l10n.set_translation(self.description_ref, text, lang)
    
    def get_description(self, lang='en'):
        """
        Returns the description in the correct language.
        """
        return l10n.get_translation(self.description_ref, lang)
    
    def is_active(self):
        return self.active    
    
    def set_full_name(self, value):
        self.full_name = value
        
    def set_handling_fee(self, cents):
        self.meta['default_handling_fee'] = cents
        
    def get_handling_fee(self):
        return self.meta.get('default_handling_fee') or 0
    
    def set_currency(self, currency):
        self.meta['default_currency'] = currency
    
    def get_currency(self):
        return self.meta.get('default_currency') or 'EUR'


class UserAccountAssociation(Base):
    
    # Meta
    
    __tablename__ = 'tickee_user_account_assoc'
    
    # Columns
    
    account_id = Column(Integer, ForeignKey('tickee_accounts.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('tickee_users.id'), primary_key=True)
    user = orm.relationship("User", backref='assocs')
    
    def __repr__(self):
        return "<UserAccountAssociation: User %s connected to Account %s>" % (self.user_id, self.account_id)