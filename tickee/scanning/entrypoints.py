from celery.task import task
from tickee.core import entrypoint
from tickee.core.security.oauth2.manager import lookup_account_for_client
from tickee.events.manager import lookup_event_by_id
from tickee.events.permissions import require_event_owner, require_eventpart_of_event
from tickee.scanning.manager import list_ticketscans
from tickee.scanning.marshalling import ticketscan_to_dict
from tickee.scanning.processing import scan_ticket
from tickee.scanning.tasks import reset_scans
from tickee.tickets.manager import lookup_ticket_by_code, list_tickets
from tickee.tickets.marshalling import ticket_to_dict
from tickee.tickets.permissions import require_tickettype_owner
import datetime
import json
import tickee.exceptions as ex
import time

@task(name="scanning.from_ticket")
@entrypoint()
def ticket_scans(client_id, ticket_code):
    """Returns a list of all scans of a ticket"""
    ticket = lookup_ticket_by_code(ticket_code)
    
    if client_id is not None:
        require_tickettype_owner(client_id, ticket.get_tickettype().id)
    
    return map(ticketscan_to_dict, ticket.scans)


@task(name="scanning.reset")
@entrypoint()
def reset_scans_e(client_id, event_id=None, eventpart_id=None, tickettype_id=None):
    """Removes all ticketscans for the event"""
    lookup_event_by_id(event_id)
    # permission restrictions
    if client_id:
        require_event_owner(client_id, event_id)
        if eventpart_id:
            require_eventpart_of_event(eventpart_id, event_id)
        if tickettype_id:
            require_tickettype_owner(client_id, tickettype_id)
    # reset
    amount = reset_scans(event_id=event_id,
                         eventpart_id=eventpart_id,
                         tickettype_id=tickettype_id)
    return dict(deleted=amount)


@task
@entrypoint()
def access_code(client_id, event_id, tickettype_id=None, eventpart_id=None, location_id=None):
    """Returns an access code which can be used by the scanner apps to 
    authenticate with the server.
    example:
        {"key":"key2","secret":"secret","event":1,"account":1,"tickettype":1,"eventpart":1}
    """ 
    lookup_event_by_id(event_id)
    
    # permission checks
    if client_id is not None:
        require_event_owner(client_id, event_id)
        if tickettype_id is not None:
            require_tickettype_owner(client_id, tickettype_id)
        if eventpart_id is not None:
            require_eventpart_of_event(eventpart_id, event_id)
    
    # build access code
    account = lookup_account_for_client(client_id)
    
    client = account.client
    access_dct = dict(key = client.key,
                      secret = client.secret,
                      event = int(event_id),
                      account = account.id)
    if eventpart_id is not None:
        access_dct['eventpart'] = int(eventpart_id)
    if tickettype_id is not None:
        access_dct['tickettype'] = int(tickettype_id)
    if location_id is not None:
        access_dct['location'] = int(location_id)
    
    return dict(access_code=json.dumps(access_dct))


@task(name="scanning.scan")
@entrypoint()
def ticket_scan_(*args, **kwargs):
    return ticket_scan(*args, **kwargs)


@task
@entrypoint()
def ticket_scan(client_id, ticket_code, scan_timestamp, extra_info={}):
    """
    Entrypoint for marking tickets as scanned and returning new updates to the
    attendees list
    
    Args:
        ticket_code:
            Hex string representing the ticket id that was scanned in.
        scan_timestamp:
            Datetime the ticket was scanned in 
        extra_info (optional):
            Dictionary containing additional information of the device.
    """
    # add ticket as scanned
    scan_datetime = datetime.datetime.utcfromtimestamp(float(scan_timestamp))
    # lookup ticket
    ticket = lookup_ticket_by_code(ticket_code)
    # assert permission to scan ticket
    if client_id is not None:
        require_tickettype_owner(client_id, ticket.get_tickettype().id)
    # exisiting scans:
    if len(ticket.scans) > 0:
        raise ex.DuplicateTicketScanError()
    # scan ticket
    scan_ticket(ticket_code, scan_datetime, extra_info)

    return True