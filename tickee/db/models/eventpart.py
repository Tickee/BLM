from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, String, DateTime, Text
from tickee.core import l10n
from tickee.tickettypes import states
import datetime
import sqlahelper
import sqlalchemy.orm as orm


Base = sqlahelper.get_base()

class EventPart(Base):
    """
    An ``Event`` can be divided into logical ``EventPart``s related to time or location.
    Examples: 
        - An ``Event`` can span several days.
        - An ``Event`` several locations each requiring differently prized tickets.
    """
    
    __tablename__ = 'tickee_eventparts'
    
    # Columns
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description_ref = Column(Integer)
    starts_on = Column(DateTime)
    ends_on = Column(DateTime)
    event_id = Column(Integer, ForeignKey('tickee_events.id'))
    venue_id = Column(Integer, ForeignKey('tickee_venues.id'))
    
    # Relations
    
    venue = orm.relationship('Venue', backref='event_parts')
    tickettypes = orm.relationship("TicketTypeEventPartAssociation", backref="eventpart")
    event = orm.relationship('Event', backref='parts')
    
    # Constructor
    
    def __init__(self, starts_on=None, ends_on=None, venue_id=None):
        """
        Construct a new ``EventPart`` object.
        """
        self.starts_on = starts_on
        self.ends_on = starts_on #ends_on
        self.venue_id = venue_id
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
    
    def get_name(self):
        if self.name is not None:
            return self.name
        else:
            return self.event.get_name()
    
    def get_tickets(self):
        """
        Get the tickets of all the ticket types connected to this event.
        """
        tickets = []
        for tickettype in self.ticket_types:
            tickets += tickettype.get_tickets()
        return tickets
    
    def get_ticket_types(self, include_inactive=False,
                               include_if_sales_finished=False):
        """
        Get the ticket types of the eventpart
        """
        tickettype_assocs = self.tickettypes
        tickettypes =  map(lambda a:a.tickettype, tickettype_assocs)
        
        # remove ticket types with finished sales
        if not include_if_sales_finished:
            tickettypes = filter(lambda tt: tt.sales_end is None or tt.sales_end >= datetime.datetime.utcnow(), tickettypes)
            
        # remove inactive ticket types
        if not include_inactive:
            tickettypes = filter(lambda tt: tt.is_active, tickettypes)
        
        return tickettypes
    
    def get_availability(self):
        """
        Derives the availability status from all the ``TicketType``s for this ``EventPart``.
        """
        currently = states.SOLD
        
        for type in self.get_ticket_types(include_inactive=False,
                                          include_if_sales_finished=True):
            # Only improve if not currently available
            if currently == states.AVAILABLE:
                return currently
            # Improve if better than SOLD
            if type.availability != states.SOLD:
                currently = type.get_availability()
        return currently
