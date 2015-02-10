from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, String, DateTime, Enum, Boolean
from tickee.core.crm.tasks import log_crm
from tickee.core.db.types import MutationDict, JSONEncodedDict
from tickee.orders.states import STARTED, TIMEOUT, PURCHASED, CANCELLED
import datetime
import hashlib
import logging
import random
import sqlahelper
import sqlalchemy.orm as orm
import tickee.exceptions as ex



Session = sqlahelper.get_session()
Base = sqlahelper.get_base()

blogger = logging.getLogger("blm.order")

class Order(Base):
    """
    An order containing various sub-orders of specific ``TicketType``s granting 
    a user an identifiable right to access a particular event.
    """
    
    __tablename__ = 'tickee_orders'
    
    # Columns
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('tickee_accounts.id'))
    order_key = Column(String(32), index=True)
    payment_key = Column(String(32), index=True)
    session_start = Column(DateTime)
    status = Column(Enum(STARTED, TIMEOUT, PURCHASED, CANCELLED, name='state_types'))
    purchased_on = Column(DateTime)
    user_id = Column(Integer, ForeignKey('tickee_users.id'))
    locked = Column(Boolean)
    payment_provider_id = Column(Integer, ForeignKey('tickee_payment_provider_info.id'))
    meta = Column(MutationDict.as_mutable(JSONEncodedDict))
    
    # Relationships
    
    account = orm.relationship('Account', backref=orm.backref("orders", lazy="dynamic"))
    user = orm.relationship('User', backref=orm.backref("orders", lazy="dynamic"))
    payment_provider = orm.relationship('PaymentProviderInformation')
    
    
    def __init__(self, user_id, account_id):
        """
        Starts an ``Order`` session.
        """
        self.status = STARTED
        self.user_id = user_id
        self.account_id = account_id
        self.touch()
        self._generate_keys()
        self.locked = False
        self.meta = {}
        
    
    def _generate_keys(self):
        while True:
            key_value = self._generate_key()
            if not Session.query(Order).filter_by(order_key=key_value).count():
                self.order_key = key_value
                break
        while True:
            key_value = self._generate_key()
            if not Session.query(Order).filter_by(payment_key=key_value).count():
                self.payment_key = key_value
                break
    
    def _generate_key(self):
        user_seed = self.user_id or random.random()*1000
        unhashed_key = str(user_seed)+str(self.session_start)+str(random.random()*1000)
        return hashlib.sha224(unhashed_key).hexdigest()[0:32]
    
    def touch(self):
        """ Resets the session timer """
        self.session_start = datetime.datetime.utcnow()
    
    def purchase(self):
        """
        Marks the ``Order`` as purchased.
        """
        if not self.is_locked():
            raise ex.OrderError("Only locked orders can be purchased.")
        self.status = PURCHASED
        self.purchased_on = datetime.datetime.utcnow()
    
    def is_purchased(self):
        return self.status == PURCHASED
    
    def is_locked(self):
        return self.locked
    
    def get_currency(self):
        if len(self.account.paymentproviders) > 0:
            return self.account.paymentproviders[0].get_info('currency')
        return None
    
    def get_events(self):
        """
        Returns all ``Event`` objects contained in this order.
        """
        events = []
        tickettypes = self.get_ticket_types()
        for tt in tickettypes:
            events.append(tt.get_event())
        return list(set(events))
        
    def get_tickets(self):
        """
        Returns all tickets that were created by this ``Order``.
        """
        tickets = []
        for ticketorder in self.ordered_tickets:
            tickets.extend(ticketorder.get_tickets())
        return tickets
    
    def get_tickets_per_event(self):
        all_tickets = self.get_tickets()
        event_tickets = dict()
        for ticket in all_tickets:
            if ticket.get_event() in event_tickets:
                event_tickets[ticket.get_event()].append(ticket)
            else:
                event_tickets[ticket.get_event()] = [ticket] 
        return event_tickets
    
    def get_ticket_count(self):
        """
        Returns the number of tickets contained in the ``Order``.
        """
        total = 0
        for ticketorder in self.get_ticketorders():
            total += ticketorder.amount
        return total
    
    def get_ticketorders(self):
        """
        Returns all ``TicketOrder`` objects associated.
        """
        return self.ordered_tickets.all()
    
    def get_ticketorders_per_event(self):
        """ Returns tickettypes related to event """
        events = dict()
        for ticketorder in self.get_ticketorders():
            event = ticketorder.ticket_type.get_event()
            if event in events:
                events[event].append(ticketorder)#events[event] = [ticketorder]#
            else:
                events[event] = [ticketorder]
        return events
        
    def get_total(self):
        """
        Calculates the total amount of the order.
        """
        total = 0
        for ticketorder in self.ordered_tickets:
            total += ticketorder.get_total()
        return total
    
    def get_handling_fee(self):
        """ Calculates the handling fee of the order in cents """
        total = 0
        for ticketorder in self.ordered_tickets:
            total += ticketorder.get_handling_fee()
        return total
    
    def cancel(self):
        """
        Marks the ``Order`` as cancelled and removes 
        all associated ``TicketOrder``s.
        """
        blogger.info("cancelling order %s" % self.id)
        log_crm("order", self.id, dict(action="cancel"))
        self.status = CANCELLED
    
    def checkout(self, user=None):
        """ Locks the order and logs the checkout in the database """
        if self.user_id is None and user is not None:
            self.user = user
        self.lock()
        blogger.info("checkout order %s" % self.id)
        log_crm("order", self.id, dict(action="checkout"))
    
    def lock(self):
        """
        Marks the ``Order`` as locked so no more tickets can be added.
        """
        blogger.debug("locking order %s" % self.id)
        if self.ordered_tickets.count() == 0:
            raise ex.EmptyOrderError("Empty orders cannot be locked.")
        if self.user_id is None:
            raise ex.OrderError('No user connected to the order.')
        self.locked = True
    
    def timeout(self):
        """
        Marks the ``Order`` as timed out and removes
        all associated ``TicketOrder``s.
        """
        blogger.debug("timeout order %s" % self.id)
        log_crm("order", self.id, dict(action="timeout"))
        self.status = TIMEOUT
        
    def get_ticket_types(self):
        """
        Returns a list of all ``TicketType``s in this order.
        """
        ticket_types = []
        for ticket_order in self.ordered_tickets:
            ticket_types.append(ticket_order.ticket_type)
        return ticket_types
    
    def update_availability(self, ticket_types=None):
        """
        Updates the availability of the ``TicketType``s in the order.
        """
        if not ticket_types:
            ticket_types = self.get_ticket_types()
        for ticket_type in ticket_types:
            ticket_type.update_availability()
    