from sqlalchemy.orm import joinedload, subqueryload
from tickee.db.models.eventpart import EventPart
from tickee.db.models.ticketorder import TicketOrder
from tickee.db.models.tickettype import TicketType, TicketTypeEventPartAssociation
from tickee.events.eventparts.manager import lookup_eventpart_by_id
from tickee.events.manager import lookup_event_by_id
from tickee.scanning.models import TicketScan
from tickee.tickets.models import Ticket
from tickee.tickets.processing import code_to_id
from tickee.tickettypes.manager import get_event_of_tickettype, lookup_tickettype_by_id
import sqlahelper
import tickee.exceptions as ex


Session = sqlahelper.get_session()

def tickets_from_order(order):
    """ Retrieves all tickets generated for an order. """
    ticketorders = order.ordered_tickets
    tickets = []
    for ticketorder in ticketorders:
        tickets += ticketorder.tickets
    return tickets

def get_event_of_ticket(ticket):
    """ Retrieves the event the ticket is connected to. """
    return get_event_of_tickettype(ticket.ticket_order.ticket_type)



def lookup_ticket_by_code(ticket_code):
    """
    Looks up a ticket by a ticket code.
    """
    ticket = Session.query(Ticket).filter(Ticket.id==code_to_id(ticket_code)).first()
    if not ticket:
        raise ex.TicketNotFoundError
    else:
        return ticket
    
def lookup_ticket_by_id(ticket_id):
    """
    Looks up a ticket by a ticket code.
    """
    ticket = Session.query(Ticket).get(ticket_id)
    if not ticket:
        raise ex.TicketNotFoundError
    else:
        return ticket
    
def list_tickets(event_id,
                 purchased_after=None,
                 eventpart_id=None,
                 tickettype_id=None):
    """
    Retrieves a list of all tickets registered to an event.
    
    Args:
        event_id:
            Filter by event.
        eventpart_id:
            Filter by eventpart.
        tickettype_id:
            Filter by tickettype.
    
    Returns:
        ???
    
    Raises:
        EventNotFoundError
        EventPartNotFoundError
        TicketTypeNotFoundError
    """
    event = lookup_event_by_id(event_id)
    # lookup tickets  
    tickets = Session.query(Ticket).join(TicketOrder)\
                     .options(subqueryload('scans', Ticket.user))
    # filter by tickettype
    if tickettype_id:
        lookup_tickettype_by_id(tickettype_id)
        tickets = tickets.filter(TicketOrder.ticket_type_id==tickettype_id)
    # filter by creation date
    tickets = tickets.join(TicketType)
    if purchased_after:
        tickets = tickets.filter(Ticket.created_at>=purchased_after)
    tickets = tickets.join(TicketTypeEventPartAssociation)
    # filter by eventpart
    if eventpart_id:
        lookup_eventpart_by_id(eventpart_id)
        tickets = tickets.filter(TicketTypeEventPartAssociation.eventpart_id==eventpart_id)
    tickets = tickets.join(EventPart)      
    # filter by event
    tickets = tickets.filter(EventPart.event_id==event_id)
    return tickets.all()