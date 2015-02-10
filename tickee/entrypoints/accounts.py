from celery.task import task
from tickee.db.models.user import UserAccountAssociation
import marshalling
import tickee.exceptions as ex
import tickee.logic as logic
import transaction

@task
def create_account(user_id, account_name, email):
    """
    Entrypoint for creating an account and returning its information back as a
    dictionary. 
    
    Args:
        user_id:
            Id of the user who will own the account
        account_name
            Name of the account to create
        email
            Email of the account. This should be a general email address
            and not a user-specific one.

    Returns:
        A dictionary containing the information of the newly created account
        including its identifier. A ``created`` key-value pair is added 
        indicating the success of the attempt. For example:
        
        {'created': True,
         'account': {"id": 42, "name": "Tickee", "email": "info@example.com"}}
         
        The dictionary will only contain the created key if the attempt was not
        successful:
        
        {'created': False}
    """
    am = logic.AccountManager()
    sm = logic.SecurityManager()
    try:
        # find user
        um = logic.UserManager()
        user = um.lookup_user_by_id(user_id)
        # create account
        account = am.create_account(account_name, email)
        # create default oauth2 client
        client = sm.create_oauth_client()
        account.client_id = client.id
    except ex.TickeeError, e:
        transaction.abort()
        # build failed result
        return marshalling.error(e)
    else:
        # connect user to account
        assoc = UserAccountAssociation()
        assoc.user = user
        account.users.append(assoc)
        
        account_info = marshalling.account_to_dict(account)
        transaction.commit()
        # build success result
        result = marshalling.created_success_dict.copy()
        result['account'] = account_info
        return result


@task
def account_exists(account_name):
    """
    Entrypoint for checking if an account already exists with a particular
    account_name.
    
    Args:
        account_name:
            The name of the account that should be checked.
    
    Returns:
        If an account exists with the passed account_name, it will return:
            {'exists': True}
        The value will be False if it does not exist.
    """
    am = logic.AccountManager()
    try:
        am.lookup_account_by_name(account_name)
    except ex.TickeeError, e:
        transaction.abort()
        return dict(exists=False)
    else:
        transaction.commit()
        return dict(exists=True)


@task
def account_info(oauth_client_id, account_id, include_events=False):
    """
    Entrypoint for viewing account information. If the account_id contains None,
    it will return the info of the account attached to the oauth client.
    
    Args:
        oauth_client_id
            Id of the OAuth2 client asking for the information.
        account_id
            The id of the account to return
        include_events
            If specified also returns a list of events owned by the account.
        
    Returns:
        A dictionary containing the information of the account
        including its identifier.
        
        {'account': 
            {"id": 42, 
             "name": "Tickee", 
             "email": "info@example.com",
             "events": [{'id': 1, 'name': 'Tickee Event'}, .. ]}}
         
        The dictionary will contain a null account if no account found:
        
        {'account': null}
    """
    am = logic.AccountManager()
    sm = logic.SecurityManager()
    try:
        if account_id:
            account = am.lookup_account_by_id(account_id)
        else:
            account = sm.lookup_account_for_client(oauth_client_id)
    except ex.TickeeError as e:
        return marshalling.error(e)
    else:
        return dict(account=marshalling.account_to_dict(account, include_events))