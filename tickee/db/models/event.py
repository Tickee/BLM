from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, String, Boolean
from tickee.core import l10n
from tickee.core.db.types import MutationDict, JSONEncodedDict
from tickee.tickettypes import states
import sqlahelper
import sqlalchemy.orm as orm

Base = sqlahelper.get_base()
Session = sqlahelper.get_session()

class Event(Base):
    """
    An event, e.g. a concert, a show, etc.
    """
    
    __tablename__ = 'tickee_events'
    
    # Columns
    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String)
    description_ref = Column(Integer)
    url = Column(String)
    image_url = Column(String)
    email = Column(String)
    
    venue_id = Column(Integer, ForeignKey('tickee_venues.id'))
    account_id = Column(Integer, ForeignKey('tickee_accounts.id'))
    
    is_public = Column(Boolean)
    is_active = Column(Boolean)
    meta = Column(MutationDict.as_mutable(JSONEncodedDict))
    
    # Relationships
    
    venue = orm.relationship('Venue', backref="events")
    account = orm.relationship('Account', backref=orm.backref('events', order_by=id))
    
    # Constructor
    
    def __init__(self, name, venue_id, account_id):
        """
        Construct a new ``Event`` object.
        """
        self.name = name
        self.venue_id = venue_id
        self.account_id = account_id
        self.is_public = True
        self.is_active = False
        self.is_private = False
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
    
    # Name
    
    def get_name(self):
        return self.name
    
    # State management

    def publish(self):
        """
        Mark the event and all tickettypes as active.
        """
        # mark event
        self.is_active = True
        # mark tickettypes
        tickettypes = self.get_ticket_types()
        map(lambda tt:tt.publish(), tickettypes)

    def unpublish(self):
        """ Marks the event as inactive """
        self.is_active = False

    def get_currency(self):
        """ Returns the currency of the account """
        return self.account.get_currency()

    def get_handling_fee(self):
        """ Returns the handling fee of the account """
        return self.account.get_handling_fee()

    def set_handling_fee(self, amount):
        """ Sets the handling fee for an event by updating all non-free tickets 
        with the new handling fee. """
        for tickettype in self.get_ticket_types(include_inactive=True):
            if not tickettype.is_free():
                tickettype.set_handling_fee(amount)

    def get_dates(self):
        """
        Returns a list of all dates when the eventparts are held.
        """
        return list(set(map(lambda ep: ep.starts_on, self.parts)))

    def get_start_date(self):
        """Returns start date of earliest eventpart"""
        start_dates = sorted(map(lambda ep: ep.starts_on, self.parts))
        if len(start_dates) > 0:
            return start_dates[0]
        return None
        
    def get_end_date(self):
        """Returns end date of latest eventpart"""
        end_dates = sorted(map(lambda ep: ep.ends_on, self.parts), reverse=True)
        if len(end_dates) > 0:
            return end_dates[0]
        return None

    def get_tickets(self):
        """
        Get the tickets of all eventparts.
        """
        tickets = []
        for eventpart in self.parts:
            tickets += eventpart.get_tickets()
        return tickets

    def get_ticket_types(self, include_inactive=False,
                               include_if_sales_finished=False):
        """
        Get the ticket types of all eventparts
        """
        tickettypes = []
        for eventpart in self.parts:
            tickettypes += eventpart.get_ticket_types(include_inactive,
                                                      include_if_sales_finished)

        return set(tickettypes)

    def get_availability(self):
        """
        Derives the availability status from all the ``TicketType``s for this ``EventPart``.
        """
        currently = states.SOLD
        for part in self.parts:
            # Only improve if not currently available
            if currently==states.AVAILABLE:
                return currently
            # Improve if better than SOLD
            if part.get_availability() != states.SOLD:
                currently = part.get_availability()
        return currently