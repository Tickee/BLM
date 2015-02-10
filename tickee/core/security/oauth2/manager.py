from pyramid_oauth2.oauth2 import datastore
import pyramid_oauth2.oauth2.exceptions as o2ex
import tickee.exceptions as ex


def lookup_account_for_client(client_id):
    """
    Retrieves the account connected to a client.
    
    Args:
        client_id:
            Id of the client
    
    Returns
        ``Account`` object related to that client.
    
    Raises:
        AccountNotFoundError
            when no client or account were found.
    """
    try:
        client = datastore.get_client_by_id(client_id)
    except o2ex.ClientNotFoundError:
        raise ex.AccountNotFoundError("Could not find an oauth2 client matching that id.")
    if not client.account:
        raise ex.AccountNotFoundError("Could not find the account connected to the oauth2 client")
    return client.account


def get_oauth_credentials(client_id):
    """
    Retrieves the oauth key/secret pair of the specific client.
    
    Args:
        client_id:
            Id of the client
            
    Returns:
        Tuple containing key and secret, e.g. ('key', 'secret')
        
    Raises:
        ClientNotFound (an OAuth2Error)
    """
    client = datastore.get_client_by_id(client_id)
    return (client.key, client.secret)