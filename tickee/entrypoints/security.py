from celery.task import task
import marshalling
import tickee.exceptions as ex
import tickee.logic as logic


@task
def get_clients(account_id, include_credentials):
    """
    Entrypoint for retrieving the oauth2 client credentials
    
    Args:
        account_id:
            Id of the account to retrieve a list his clients and their 
            credentials
    
    Returns:
        A dictionary containing a key "clients" with a list of client information
        including their credentials 
        
        {'clients': [{'id': 5, 'name': 'Access Application',
                      'key': 'thisisakey', 'secret': 'thisisasecret'}, .. ]}
                      
        If no account was found, the list will be empty:
        
        {'clients': []}
    """
    sm = logic.SecurityManager()
    try:
        clients = sm.get_clients(account_id)
    except ex.AccountNotFoundError:
        client_list = list()
    else:
        # build result
        client_list = map(lambda x: marshalling.client_to_dict(x, include_credentials), 
                          clients)
    return dict(clients=client_list)