# -*- coding: utf-8 -*-

from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, DateTime
import datetime
import sqlahelper
import calendar

Base = sqlahelper.get_base()

class Ticket(Base):
    """
    Part of an ``Order`` describing an intent to purchase a number of units of
    a ``TicketType``.
    """
    
    __tablename__ = 'tickee_tickets'
    
    # Columns
    
    id = Column(Integer, primary_key=True)
    ticket_order_id = Column(Integer, ForeignKey('tickee_ticketorders.id'))
    user_id = Column(Integer, ForeignKey('tickee_users.id')) # owner of the ticket
    created_at = Column(DateTime)
    
    # Relations
    
    user = relationship('User', backref=backref('tickets', lazy="dynamic"))
    ticket_order = relationship('TicketOrder', backref="tickets")
    
    # Constructor
    
    def __init__(self, ticket_order_id, user_id):
        self.ticket_order_id = ticket_order_id
        self.user_id = user_id
        self.created_at = datetime.datetime.utcnow()
      
    # Slug
    
    def slugify(self):
        return "%s:%s:%s" % (self.get_code(), 
                             int(calendar.timegm(self.created_at.timetuple())),
                             self.user_id)
    
    def get_tickettype(self):
        """
        Returns the ``TicketType`` associated with this ticket.
        """
        return self.ticket_order.ticket_type
    
    def get_price(self):
        """
        Returns the price of the ticket, without handling fee.
        """
        return self.get_tickettype().get_price()
    
    def get_code(self):
        """
        Returns a unique code for the ticket.
        """
        return "%09X" % self.id
    
    def get_qr_code_information(self):
        """
        Returns what information has to be put into the QR code.
        """
        info = u'{{"key":"{0}:{1}:{2}","ical":"http://tick.ee/"}}'.format(self.get_code(), 
                                                                          int(calendar.timegm(self.created_at.timetuple())),
                                                                          self.get_owner().id)
        return info
    
    def get_buyer(self):
        """
        Returns the ``User`` object who bought the ticket.
        """
        return self.user
        
    def get_owner(self):
        """
        Returns the ``User`` object who owns the ticket. Since tickets may
        be traded, this is possible.
        """
        return self.ticket_order.order.user
    
    def get_event(self):
        """ Returns the event corresponding to the ticket """
        return self.ticket_order.ticket_type.get_event()
    
    def is_scanned(self):
        """
        Returns a boolean indicating if the ticket has been scanned.
        """
        if self.scans:
            return True
        else:
            return False