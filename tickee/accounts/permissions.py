from tickee.accounts.manager import lookup_account_by_id
from tickee.core.security.oauth2.manager import lookup_account_for_client
from tickee.exceptions import AccountNotFoundError, PermissionDenied, EventNotFoundError

def require_account_owner(client_id, account):
    """Checks if the account of the requesting client id is the event owner.
    """
    try:
        client_account = lookup_account_for_client(client_id)
    except AccountNotFoundError:
        raise PermissionDenied("No account connected to your client.")
    # validate if event is connected to account
    if account != client_account: 
        raise PermissionDenied("You are not the owner of the account.")