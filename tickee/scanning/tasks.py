from tickee.db.models.eventpart import EventPart
from tickee.db.models.ticketorder import TicketOrder
from tickee.db.models.tickettype import TicketType, TicketTypeEventPartAssociation
from tickee.scanning.models import TicketScan
from tickee.tickets.models import Ticket
import sqlahelper

Session = sqlahelper.get_session()

def reset_scans(**filters):
    """Removes all ticket scans for an event, eventpart or tickettype
    
    Arguments:
        event_id: integer identifying the event
        eventpart_id: integer identifying the eventpart
        tickettype_id: integer identifying the tickettype
        
    Returns:
        the amount of ticketscans that were removed
    """
    # validate if all 
    query = Session.query(TicketScan)
    # filter by tickettype_id
    tickettype_id = filters.get('tickettype_id')
    query = query.join(Ticket).join(TicketOrder)
    if tickettype_id:
        query = query.filter(TicketOrder.ticket_type_id==tickettype_id)
    # filter by eventpart
    eventpart_id = filters.get('eventpart_id')
    query = query.join(TicketType).join(TicketTypeEventPartAssociation)
    if eventpart_id:
        query = query.filter(TicketTypeEventPartAssociation.eventpart_id==eventpart_id)
    # filter by event
    event_id = filters.get('event_id')
    query = query.join(EventPart)
    if event_id:
        query = query.filter(EventPart.event_id==event_id)
    tickets_to_be_removed = query.all()
    for ticket in tickets_to_be_removed:
        Session.delete(ticket)
    Session.flush()
    return len(tickets_to_be_removed)