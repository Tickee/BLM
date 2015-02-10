from celery.task import task
from tickee.accounts.manager import lookup_account_by_name, lookup_account_by_id, \
    lookup_accounts_of_user
from tickee.accounts.marshalling import account_to_dict, account_to_dict2
from tickee.accounts.processing import create_account
from tickee.accounts.tasks import send_account_welcome_mail
from tickee.core import entrypoint
from tickee.core.security.oauth2.manager import lookup_account_for_client
from tickee.core.security.oauth2.processing import create_oauth_client
from tickee.db.models.account import UserAccountAssociation
from tickee.exceptions import AccountError, AccountNotFoundError
from tickee.paymentproviders.processing import \
    create_payment_provider_information
from tickee.paymentproviders.tasks import create_payment_provider
from tickee.subscriptions.models import Subscription, FREE
from tickee.users.manager import lookup_user_by_id
import logging

tlogger = logging.getLogger('technical')

@task(name='accounts.deactivate')
@entrypoint()
def account_deactivate(account_name):
    """ Deactivates the account """
    account = lookup_account_by_name(account_name)
    account.is_active = False
    return account_to_dict(account)


@task(name='accounts.create')
@entrypoint()
def account_create(user_id, account_info):
    """
    Entrypoint for creating an account and returning its information back as a
    dictionary. 
    
    Args:
        user_id:
            Id of the user who will own the account
        account_info:
            Dictionary containing the following keys:
                -  short_name (required)
                -  email (required)
                -  name
                -  url
                -  vat
                -  subtitle
                -  handling_fee
    """
    # create account
    account = create_account(account_info.get('short_name'), 
                             account_info.get('email'))
    # add optional information
    account.full_name = account_info.get('name')
    account.website = account_info.get('url')
    account.vat_percentage = account_info.get('vat')
    account.meta['subtitle'] = account_info.get('subtitle')
    account.meta['theme'] = account_info.get('theme')
    account.set_handling_fee(account_info.get('handling_fee') or 0)
    # add default subscription
    account.subscription = Subscription(FREE)
    # create default oauth2 client
    client = create_oauth_client()
    account.client_id = client.id
    # connect user to account
    user = lookup_user_by_id(user_id)
    assoc = UserAccountAssociation()
    assoc.user = user
    assoc.account_id = account.id
    account.users.append(assoc)
    # set preferred payment service provider
    account.meta['preferred_psp'] = account_info.get('preferred_psp')
    # create psp object
    create_payment_provider(account, {}, account_info.get('preferred_psp'))
    # set currency
    account.set_currency(account_info.get('currency'))
    # send account welcome mail
    send_account_welcome_mail.apply_async(args=[user.id, account.id], countdown=10)
    
    account_info = account_to_dict(account)
    return account_info


@task(name="accounts.update")
@entrypoint()
def account_update(account_identifier, account_info):
    """ Replaces a account's data with the information located in account_info """
    print account_info
    try:
        account = lookup_account_by_name(account_identifier)
    except:
        account = lookup_account_by_id(int(account_identifier))
    for (key, value) in account_info.iteritems():
        if value is None:
            continue # skip unset fields
        if key == "name":
            account.full_name = value
        elif key == "email":
            account.email = value
        elif key == "url":
            account.website = value.replace('https://', '').replace('http://', '')
        elif key == "vat":
            account.vat_percentage = value
        elif key == "subtitle":
            account.meta['subtitle'] = value
        elif key == "handling_fee":
            account.set_handling_fee(value)
        elif key == "currency":
            account.set_currency(value)
        elif key == "theme":
            account.meta['theme'] = value
        elif key == "phone":
            account.meta['phone'] = value
        elif key == "vatnumber":
            account.meta['vatnumber'] = value
        elif key == "social":
            account.meta['social'] = value
        elif key == "ext":
            account.meta['ext'] = value
        else:
            tlogger.error('received unknown information when updating account %s: %s' % (account_identifier, key))
    return account_to_dict(account, True, True )


@task(name='accounts.exists')
@entrypoint(on_exception=False)
def account_exists(account_name, include_inactive=False):
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
    account = lookup_account_by_name(account_name)
    if include_inactive or account.is_active():
        return account_to_dict2(account)
    else:
        return False


@task(name='accounts.details')
@entrypoint()
def account_info(oauth_client_id, account_id=None, account_shortname=None):
    """
    Entrypoint for viewing account information. If the account_id contains None,
    it will return the info of the account attached to the oauth client.
    
    Args:
        oauth_client_id
            Id of the OAuth2 client asking for the information.
        account_id
            The id of the account to return
        
    Returns:
        A dictionary containing the information of the account
        including its identifier.
        
        {
            "id": 42, 
            "name": "Tickee", 
            "email": "info@example.com"
        }
         
    """
    if account_id is not None:
        account = lookup_account_by_id(account_id)
    elif account_shortname is not None:
        account = lookup_account_by_name(account_shortname)
    else:
        account = lookup_account_for_client(oauth_client_id)
    
    if account.is_active():
        return account_to_dict(account, include_theme=True, include_social=True )
    else:
        return AccountNotFoundError()



@task(name='accounts.list_accounts')
@entrypoint()
def list_accounts(user_id=None, include_inactive=False):
    """ Returns a list of all accounts connected to the user."""
    user = lookup_user_by_id(user_id)
    accounts = lookup_accounts_of_user(user, include_inactive=include_inactive)
    return map(account_to_dict, accounts)


@task(name='accounts.keys')
@entrypoint()
def account_client_keys(client_id, account_short):
    """ Returns a list of all key/secrets connected to the account """
    account = lookup_account_by_name(account_short)
    if account.is_active():
        return [dict(key=account.client.key,
                     secret=account.client.secret)]
    else:
        raise AccountError("The account is not active.")