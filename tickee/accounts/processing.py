from sqlalchemy.exc import IntegrityError, FlushError
from tickee.accounts.manager import lookup_account_by_id
from tickee.db.models.account import Account, UserAccountAssociation
from tickee.users.manager import lookup_user_by_id
import sqlahelper
import tickee.exceptions as ex

Session = sqlahelper.get_session()

def create_account(account_name, email):
    """Creates and saves an inactive account with the given account name, email.

    Args:
        account_name: 
            Unique account name (use :func:`api.account.unique` to confirm).
        email: 
            Valid e-mail address, checking should happen front-end.
    
    Returns:
        The newly created account object
        
    Raises:
        AccountError
            An account with that name already exists
    """
    account = Account(account_name, email)
    account.active = True
    Session.add(account)
    try:
        Session.flush()
    except IntegrityError as e:
        raise ex.AccountError("The account name already exists")
    return account


def add_user(account_id, user_id):
    """
    Adds a user to the account.
    
    Args:
        account_id:
            The id of the account the user will belong to.
        user_id:
            The id of the user to add to the account.
            
    Raises:
        AccountNotFoundError:
            No account was found matching the account_id
        UserNotFoundError:
            No user was found matching the user_id
        UserAssociationError:
            The user is already associated wit the account
    """
    # lookup account
    account = lookup_account_by_id(account_id)
    # lookup user
    user = lookup_user_by_id(user_id)
    # add the user to the account
    assoc = UserAccountAssociation()
    assoc.user = user
    account.users.append(assoc)
    try:
        Session.flush()
    except FlushError:
        raise ex.UserAssociationError("The user is already associated wit the account")