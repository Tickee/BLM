from celery.task import task
from tickee.entrypoints.marshalling import ticket_to_dict
from tickee.events.permissions import require_event_owner
from tickee.scanning.manager import list_ticketscans
from tickee.scanning.marshalling import ticketscan_to_dict
from tickee.tickets.permissions import require_tickettype_owner
import datetime
import marshalling
import tickee.exceptions as ex
import tickee.logic as logic
import time
import transaction


@task
def create_ticket(eventpart_id, ticket_price, ticket_units, 
                  ticket_currency="EUR", ticket_name="Ticket"):
    tm = logic.TicketManager()
    # create ticket type
    try:
        tickettype = tm.create_ticket_type(eventpart_id, ticket_price, ticket_units, 
                                   ticket_name, ticket_currency)
    except ex.EventPartNotFoundError:
        transaction.abort()
        # build failure result
        result = marshalling.created_failed_dict
    else:
        transaction.commit()
        # build success result
        result = marshalling.created_success_dict()
        result['tickettype'] = marshalling.tickettype_to_dict(tickettype)
    return result



@task
def scan_ticket(client_id, ticket_code, scan_datetime, list_timestamp, 
                list_event_id, list_eventpart_id=None, list_tickettype_id=None, extra_info={}):
    """
    Entrypoint for marking tickets as scanned and returning new updates to the
    attendees list
    
    Args:
        ticket_code:
            Hex string representing the ticket id that was scanned in.
        scan_datetime:
            Datetime the ticket was scanned in 
        list_timestamp:
            Datetime containing the time the attendees list was last updated
        list_event_id:
            Id of the event to return updates from
        list_eventpart_id (optinal):
            Id of the eventpart to return updates from
        list_tickettype_id (optional):
            Id of the tickettype to return updates from
        extra_info (optional):
            Dictionary containing additional information of the device.
    """
    
    tm = logic.TicketManager()
    # add ticket as scanned
    try:
        scan_datetime = datetime.datetime.strptime(scan_datetime, "%Y-%m-%dT%H:%M:%S")
        list_timestamp = datetime.datetime.fromtimestamp(float(list_timestamp))
        # lookup ticket
        ticket = tm.lookup_ticket_by_code(ticket_code)
        # assert permission to scan ticket
        require_tickettype_owner(client_id, ticket.get_tickettype().id)
        # scan ticket
        tm.scan_ticket(ticket_code, scan_datetime, extra_info)
    except ex.TickeeError, e:
        transaction.abort()
        result = marshalling.error(e)
    else:
        # fetch updates to attendees
        result = dict(scanned=True)
        result['updates'] = map(lambda ts: ticketscan_to_dict(ts),
                                list_ticketscans(event_id=list_event_id, 
                                                eventpart_id=list_eventpart_id, 
                                                tickettype_id=list_tickettype_id, 
                                                scanned_after=list_timestamp))
        result['new_tickets'] = map(lambda t: ticket_to_dict(t, include_user=True),
                                    tm.list_tickets(event_id=list_event_id,
                                                 eventpart_id=list_eventpart_id,
                                                 tickettype_id=list_tickettype_id,
                                                 purchased_after=list_timestamp))
        result['timestamp'] = int(time.time())
        transaction.commit()
    return result



@task
def list_tickets(client_id, event_id, eventpart_id=None, tickettype_id=None):
    """
    Entrypoint for listing all tickets of an event. If eventpart is sent with,
    it will only show all attendees of the eventpart.
    
    Args:
        client_id:
            Id of the requesting client
        event_id:
            Id of the event
        eventpart_id (optional):
            Id of the eventpart to show.
        tickettype_id (optional):
            Id of the tickettype to show.
            
    Returns:
        A dictionary containing a list of user dictionaries that own a ticket 
        for the event.
    """  
    
    tm = logic.TicketManager()
    try:
        require_event_owner(client_id, event_id)
        tickets = tm.list_tickets(event_id=event_id, 
                                  eventpart_id=eventpart_id, 
                                  tickettype_id=tickettype_id)
    except ex.TickeeError, e:
        transaction.abort()
        return marshalling.error(e)
    else:
        result = dict()
        result['tickets'] = map(lambda t: marshalling.ticket_to_dict(t, 
                                                                     include_scanned=True), 
                                tickets)
        result['timestamp'] = int(time.time())
        transaction.commit()
        return result