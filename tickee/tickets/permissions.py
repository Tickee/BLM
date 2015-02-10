from tickee.core.security.oauth2.manager import lookup_account_for_client
from tickee.exceptions import AccountNotFoundError, PermissionDenied, TicketTypeNotFoundError
from tickee.tickettypes.manager import lookup_tickettype_by_id

def require_tickettype_owner(client_id, tickettype_id):
    """Checks if the account of the requesting client id is the 
    tickettype owner.
    """
    try:
        account = lookup_account_for_client(client_id)
        tickettype = lookup_tickettype_by_id(tickettype_id)
    except AccountNotFoundError:
        raise PermissionDenied("Your client is not connected to an account.")
    except TicketTypeNotFoundError:
        raise PermissionDenied("The tickettype you requested does not exist.")
    # validate if event is connected to account
    if tickettype.get_event().account_id != account.id:
        raise PermissionDenied("You are not the owner of the tickettype.")