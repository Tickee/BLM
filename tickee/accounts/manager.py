from tickee.db.models.account import Account
import sqlahelper
import tickee.exceptions as ex

Session = sqlahelper.get_session()

def lookup_account_by_id(account_id):
    """
    Retrieves the account with the given id.
    
    Args:
        account_id:
            The id of the account to return
            
    Returns:
        ``Account`` object connected to the account_id
        
    Raises:
        AccountNotFoundError 
            No account was found matching the account_id.
    """
    account = Session.query(Account).get(account_id)
    if not account:
        raise ex.AccountNotFoundError()
    return account


def lookup_account_by_name(account_name):
    """
    Retrieves the account with the given name.
    
    Args:
        account_name:
            The name of the account to return
            
    Returns:
        ``Account`` object connected to the account_name
        
    Raises:
        AccountNotFoundError 
            No account was found matching the account_name.
    """
    account = Session.query(Account).filter(Account.name==account_name).first()
    if not account:
        raise ex.AccountNotFoundError()
    return account

def lookup_user_associations_of_account(account_id):
    """
    Lists all associations to an account.
    
    Args:
        account_id:
            The id of the account the users are associated to.
    
    Returns:
        A list of ``UserAccountAssociation`` associated with the account.
        
    Raises:
        AccountNotFoundError:
            No account was found matching the account_id
    """
    # lookup acount
    account = lookup_account_by_id(account_id)
    # find associations
    return account.users


def lookup_accounts_of_user(user, include_inactive=False):
    """ Returns a list of all accounts connected to the user """
    account_assocs = user.assocs
    all_accounts = map(lambda assoc:assoc.account, account_assocs)
    if include_inactive:
        return all_accounts
    else:
        return filter(lambda a: a.is_active(), all_accounts)