from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.sql.functions import sum, coalesce
from sqlalchemy.types import Integer, String, Enum, Text, Boolean, DateTime
from tickee.core import l10n
from tickee.db.models.order import Order
from tickee.db.models.ticketorder import TicketOrder
from tickee.orders.states import TIMEOUT, CANCELLED, PURCHASED
from tickee.tickets.models import Ticket
from tickee.tickettypes.states import AVAILABLE, CLAIMED, SOLD
import logging
import sqlahelper
import sqlalchemy.orm as orm

Session = sqlahelper.get_session()
Base = sqlahelper.get_base()

blogger = logging.getLogger("blm.tickettype")


class TicketTypeEventPartAssociation(Base):
    
    # Meta
    
    __tablename__ = 'tickee_tickettype_eventpart_assoc'
    
    # Columns
    
    tickettype_id = Column(Integer, ForeignKey('tickee_tickettypes.id'), primary_key=True)
    eventpart_id = Column(Integer, ForeignKey('tickee_eventparts.id'), primary_key=True)
    
    tickettype = orm.relationship("TicketType", backref="assocs")

    def __repr__(self):
        return "<TicketTypeEventPartAssociation: TicketType %s connected to EventPart %s>"\
               % (self.tickettype_id, self.eventpart_id)



class TicketType(Base):
    """
    A type of tickets available for a specific ``EventPart``. Each ``TicketType`` can 
    have a specific price and amount available units.
    """
    
    __tablename__ = 'tickee_tickettypes'
    
    # Columns
    
    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String)
    description_ref = Column(Integer)
    
    price = Column(Integer) # in cents
    handling_fee = Column(Integer) # in cents
    
    units = Column(Integer)
    min_units_order = Column(Integer)
    max_units_order = Column(Integer)
    sales_start = Column(DateTime)
    sales_end = Column(DateTime)
    
    is_active = Column(Boolean)
    availability = Column(Enum(AVAILABLE, CLAIMED, SOLD, name='availability_type'))
    
    currency_id = Column(String, ForeignKey('tickee_currencies.name'))
    
    # Relations
    
    currency = orm.relationship('Currency')
    
    # Constructor
    
    def __init__(self, name, price, currency, units):
        """
        Construct a new ``TicketType`` object.
        """
        self.name = name
        self.price = price
        self.currency_id = currency
        self.units = units
        self.is_active = False
        self.availability = AVAILABLE
        self.description_ref = l10n.create_text_localisation().reference_id
    
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
    
    # Methods
    
    def publish(self):
        """
        Set ticket as active
        """
        blogger.debug("publishing tickettype %s", self.id)
        self.is_active = True
    
    def unpublish(self):
        """
        Set the ticket as inactive
        """
        blogger.debug("unpublishing tickettype %s" % self.id)
        self.is_active = False
    
    def get_event(self):
        """
        Returns the event this ticket belongs to.
        """
        assocs = self.assocs
        if len(assocs) > 0:
            return assocs[0].eventpart.event
        return None
        
    def get_handling_fee(self):
        """ Returns the handling fee for this ticket """
        # free tickets do not have handling fees
        if self.is_free():
            return 0
        # specific handling fee is set for this tickettype
        elif self.handling_fee is not None:
            return self.handling_fee
        # look at event for handling fee
        else:
            return self.get_event().get_handling_fee()
    
    def set_handling_fee(self, amount):
        """
        Sets handling fee
        """
        blogger.debug("Setting handling fee for tickettype %s to %s %s cents.", 
                      self.id, self.currency_id, amount)
        self.handling_fee = amount
    
    
    def get_price(self):
        return self.price
    
    def get_full_price(self):
        return self.price + self.get_handling_fee()
    
    
    def get_tickets(self):
        """
        Get the purchased tickets of this ticket type.
        """
        return Session.query(Ticket).join(TicketOrder)\
                                    .join(TicketType)\
                                    .filter(TicketType.id==self.id)
    
    def has_available(self, ticket_amount):
        """
        Checks whether a specific amount of tickets can still be bought.   
        """
        print "checking: available amount %s >= requested amount %s" % (self.amount_available_tickets(), ticket_amount)
        return self.amount_available_tickets() >= ticket_amount 
    
    
    def amount_available_tickets(self):
        """
        Retrieve the amount of tickets still available for purchase.
        """
        return self.units - self.amount_ordered_tickets()
    
    
    def amount_ordered_tickets(self):
        """
        Retrieve the amount of tickets in ``TicketOrder``s.
        """
        result = Session.query(coalesce(sum(TicketOrder.amount), 0))\
                        .join(Order)\
                        .filter(~Order.status.in_([TIMEOUT, CANCELLED]))\
                        .filter(TicketOrder.ticket_type_id==self.id).first()
        return result[0]
    
    def amount_purchased_tickets(self):
        """
        Retrieves the amount of purchased tickets in ``TicketOrder``s. 
        """
        result = Session.query(sum(TicketOrder.amount))\
                        .filter(TicketOrder.ticket_type_id==self.id)\
                        .join(Order)\
                        .filter(Order.status==PURCHASED).first()
        return result[0]
    
    def is_free(self):
        return self.price == 0
    
    def get_availability(self):
        """Returns the availability of the tickettype"""
        return self.availability
        
    
    def update_availability(self):
        """
        Adjusts the availability if necessary.
        """
        if self.availability == AVAILABLE:
            # AVAILABLE --> CLAIMED
            if self.amount_available_tickets() <= 0:
                blogger.info("tickettype %s is now CLAIMED.", self.id)
                self.availability = CLAIMED
                return
        
        elif self.availability == CLAIMED:
            # CLAIMED --> SOLD
            if self.amount_purchased_tickets() >= self.units:
                print "purchased:", self.amount_purchased_tickets()
                blogger.info("tickettype %s is now SOLD.", self.id)
                self.availability = SOLD
                return
        
            # CLAIMED --> AVAILABLE
            if self.amount_available_tickets() > 0:
                blogger.info("tickettype %s is now AVAILABLE again.", self.id)
                self.availability = AVAILABLE
                return
        
        elif self.availability == SOLD:
            # SOLD -> AVAILABLE
            if self.amount_available_tickets() > 0:
                blogger.info("tickettype %s is now AVAILABLE again.", self.id)
                self.availability = AVAILABLE
                return
            
        blogger.debug("no state change to tickettype necessary")

    
    
#    def amount_purchased_tickets(self):
#        """
#        Retrieve the amount of tickets in ``TicketOrder`` sessions that are 
#        confirmed as purchased
#        
#        TODO: this might be able to be done in a SUM() query
#        """
#        orders = self.purchased_orders()
#        return sum(map(lambda x:x.amount, list(orders)))
#      
#      
    # Ticket Orders Sessions
#    
#    def amount_started_sessions(self):
#        """
#        Retrieve the amount of ``TicketOrder`` sessions that are currently 
#        started. 
#        """
#        return self.active_orders().count()
#    
#    
#    def amount_timedout_sessions(self):
#        """
#        Retrieve the amount of ``TicketOrder`` sessions that have 
#        timed out. 
#        """
#        return self.timedout_orders().count()
    
#    
#    def active_orders(self):
#        """
#        Retrieve a query of all the ``TicketOrder`` sessions that 
#        have not timed out.
#        """
#        return self.orders.filter(TicketOrder.status.in_([STARTED, PURCHASED]))
#    
#    
#    def purchased_orders(self):
#        """
#        Retrieve a query of all the ``TicketOrder`` sessions that are
#        currently confirmed as purchased.
#        """
#        return self._get_orders_by_status(PURCHASED)
#    
#    
#    def started_orders(self):
#        """
#        Retrieve a query of all the ``TicketOrder`` sessions that are 
#        currently started.
#        """
#        return self._get_orders_by_status(STARTED)
#    
#    
#    def timedout_orders(self):
#        """
#        Retrieve a query of all the ``TicketOrder`` sessions that have
#        timed out.
#        """
#        return self._get_orders_by_status(TIMEOUT)
#    
#    
#    # Internal
#    
#    def _get_orders_by_status(self, status=PURCHASED):
#        """
#        Retrieve a query of ``TicketOrder``s that have a specific status.
#        """
#        return self.orders.filter_by(status=status)