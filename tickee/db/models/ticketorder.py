from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer
import logging
import sqlahelper

Base = sqlahelper.get_base()
Session = sqlahelper.get_session()

blogger = logging.getLogger("blm")

class TicketOrder(Base):
    """
    Part of an ``Order`` describing an intent to purchase a number of units of
    a ``TicketType``.
    """
    
    __tablename__ = 'tickee_ticketorders'
    
    # Columns
    
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer)
    ticket_type_id = Column(Integer, ForeignKey('tickee_tickettypes.id'))
    order_id = Column(Integer, ForeignKey('tickee_orders.id'))
    
    # Relations
    
    ticket_type = relationship('TicketType', backref="ticket_orders")
    order = relationship('Order', backref=backref('ordered_tickets', lazy='dynamic'))
    
    # Constructor
    
    def __init__(self, order_id, ticket_type_id, amount):
        """
        Construct a new ``TicketOrder`` object.
        """
        self.order_id = order_id
        self.ticket_type_id = ticket_type_id
        self.amount= amount
        
    # Methods
    
    def get_tickets(self):
        """
        Returns all tickets that were created by this ``TicketOrder``.
        """
        return list(self.tickets)
    
    def get_total(self):
        """
        Calculates the total amount of this ``TicketOrder``.
        """
        return self.amount * self.ticket_type.get_full_price()

    def get_handling_fee(self):
        """ Calculates the handling fee amount in cents """
        return self.amount * self.ticket_type.get_handling_fee()
