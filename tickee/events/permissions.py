from tickee.core.security.oauth2.manager import lookup_account_for_client
from tickee.events.eventparts.manager import lookup_eventpart_by_id
from tickee.events.manager import lookup_event_by_id
from tickee.exceptions import PermissionDenied, AccountNotFoundError, EventNotFoundError, EventPartNotFoundError

 
def require_event_owner(client_id, event_id):
    """Checks if the account of the requesting client id is the event owner.
    """
    try:
        account = lookup_account_for_client(client_id)
        event = lookup_event_by_id(event_id)
    except AccountNotFoundError:
        raise PermissionDenied("Your client is not connected to an account.")
    except EventNotFoundError:
        raise PermissionDenied("The event you requested does not exist.")
    # validate if event is connected to account
    if event.account_id != account.id: 
        raise PermissionDenied("You are not the owner of the event.")
    
def require_eventpart_owner(client_id, eventpart_id):
    """Checks if the account of the requesting client id is the event owner.
    """
    try:
        account = lookup_account_for_client(client_id)
        eventpart = lookup_eventpart_by_id(eventpart_id)
        event = lookup_event_by_id(eventpart.event_id)
    except AccountNotFoundError:
        raise PermissionDenied("Your client is not connected to an account.")
    except EventNotFoundError:
        raise PermissionDenied("The eventpart you requested does not exist.")
    # validate if event is connected to account
    if event.account_id != account.id: 
        raise PermissionDenied("You are not the owner of the eventpart.")    
    
    
def require_eventpart_of_event(eventpart_id, event_id):
    """Checks if the eventpart belongs to the event."""
    try:
        eventpart = lookup_eventpart_by_id(eventpart_id)
        event = lookup_event_by_id(event_id)
    except EventPartNotFoundError:
        raise PermissionDenied("The eventpart you requested does not exist.")
    except EventNotFoundError:
        raise PermissionDenied("The event you requested does not exist.")
    # validate if the eventpart is connected to the event
    if eventpart.event.id != event.id:
        raise PermissionDenied("The eventpart is not connected to the event.")