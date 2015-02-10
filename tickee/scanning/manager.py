from tickee.db.models.eventpart import EventPart
from tickee.db.models.ticketorder import TicketOrder
from tickee.db.models.tickettype import TicketType, TicketTypeEventPartAssociation
from tickee.scanning.models import TicketScan
from tickee.tickets.models import Ticket
import sqlahelper

Session = sqlahelper.get_session()

def list_ticketscans(event_id=None, eventpart_id=None, 
                     tickettype_id=None, 
                     scanned_after=None):
    """Retrieves a list of ticketscans"""
    ticketscans = Session.query(TicketScan)
    # filter by scan_date
    if scanned_after:
        ticketscans = ticketscans.filter(TicketScan.scanned_date>=scanned_after)
    ticketscans = ticketscans.join(Ticket, TicketOrder)    
    # filter tickettype
    if tickettype_id:
        ticketscans = ticketscans.filter(TicketOrder.ticket_type_id==tickettype_id)
    ticketscans = ticketscans.join(TicketType, TicketTypeEventPartAssociation)
    # filter eventpart
    if eventpart_id:
        ticketscans = ticketscans.filter(TicketTypeEventPartAssociation.eventpart_id==eventpart_id)
    ticketscans = ticketscans.join(EventPart)
    # filter event
    if event_id:
        ticketscans = ticketscans.filter(EventPart.event_id==event_id)
    return ticketscans.all()
    