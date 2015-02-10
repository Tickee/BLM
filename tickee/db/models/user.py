# -*- coding: utf-8 -*-
'''
Created on Jul 5, 2011

@author: kevin
'''
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String, DateTime, Unicode
from tickee.core.db.types import MutationDict, JSONEncodedDict
from tickee.core.marshalling import date, json_to_date
from urllib import quote_plus
import datetime
import logging
import sqlahelper

Base = sqlahelper.get_base()
Session = sqlahelper.get_session()

blogger = logging.getLogger("blm.user")

UNUSABLE_PASSWORD = "!"


class User(Base):
    
    # Meta
    
    __tablename__ = 'tickee_users'
    
    # Columns
    
    id = Column(Integer, primary_key=True)
    first_name = Column(Unicode(30))
    last_name = Column(Unicode(30))
    email = Column(String(60), unique=True)
    password = Column(String)
    activation_key = Column(String(16))
    date_joined = Column(DateTime)
    last_login = Column(DateTime)
    meta = Column(MutationDict.as_mutable(JSONEncodedDict))
    
    # Constructor
    
    def __init__(self, email):
        self.email = email
        self.date_joined = datetime.datetime.utcnow()
        self.meta = dict()
    
    def get_full_name(self):
        name = u"{0} {1}".format(self.first_name, self.last_name)
        return name
    
    # Slug
    
    def slugify(self):
        return quote_plus(self.email)
    
    # Activation related
        
    def is_active(self):
        """
        Returns True if user is active.
        """
        return self.activation_key is None
    
    def activate(self):
        """
        Activates the user.
        """
        self.activation_key = None
        blogger.debug("activated user %s" % self.id)
        
    def deactivate(self):
        """
        Deactivates the user.
        """
        self.activation_key = self._generate_activation_key()
        blogger.debug("deactivated user %s" % self.id)
        
    def reset(self):
        """
        Marks the user as inactive and generates a new activation key.
        """
        self.password = UNUSABLE_PASSWORD
        self.deactivate()
        blogger.debug("resetting user %s." % self.id)
        
    def _generate_activation_key(self):
        from random import choice
        allowed_chars = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ0123456789"
        while True:
            key_value = ''.join([choice(allowed_chars) for i in range(8)])
            if not Session.query(User).filter_by(activation_key=key_value).count():
                return key_value
    
    # Password recovery
    
    def create_recovery_code(self):
        """ Creates an opportunity to recover the password """
        self.meta['recovery'] = dict(code=self._generate_activation_key(),
                                     deadline=date(datetime.datetime.utcnow()+datetime.timedelta(hours=48)))
        return self.meta['recovery']
        
    def remove_recovery_code(self):
        """ Removes the existing recovery code and time window """
        if "recovery" in self.meta:
            del self.meta['recovery']
    
    def get_recovery_code(self):
        """ Returns the recovery code if any exists """
        return self.meta['recovery'].get('code')
    
    def has_recovery_window(self):
        """ Checks if the user can currently recover his password. """
        return "recovery" in self.meta
    
    def is_valid_recovery_code(self, code):
        """ Checks if the code is correct and still in a valid time window """
        return (code == self.meta.get('recovery', {}).get('code', False)\
                and datetime.datetime.utcnow() <= json_to_date(self.meta['recovery'].get('deadline')))
            
    # Password related
        
    def set_password(self, raw_password):
        """
        Sets a new password.
        """
        import os, base64
        algo = "ssha"
        salt = unicode.lower(unicode(base64.b16encode(os.urandom(4))))
        hsh = self._encrypt_password(algo, salt, raw_password)
        self.password = '%s$%s$%s' % (algo, salt, hsh)
    
    def check_password(self, raw_password):
        """
        Validates the raw_password to the one in the database.
        """
        if self.has_usable_password():
            algo, salt, hsh = self.password.split("$")
            return hsh == self._encrypt_password(algo, salt, raw_password)
        return False
    
    def has_usable_password(self):
        """
        Checks whether the user has a password set.
        """
        return self.password != UNUSABLE_PASSWORD
    
    def _encrypt_password(self, algo, salt, raw_password):
        """
        Encrypts the raw_password for safe storage in the database.
        """
        if algo == "ssha":
            import base64, hashlib
            raw_salt = base64.b16encode(unicode.upper(salt))
            return hashlib.sha1(raw_password + raw_salt).hexdigest()
        raise ValueError('Got unknown password algorithm type.')