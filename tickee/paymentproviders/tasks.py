from tickee.core.validators import validate_email, ValidationError
from tickee.orders.manager import lookup_order_by_key
from tickee.paymentproviders.manager import lookup_payment_provider_for_order
import logging
import sqlahelper
import tickee.exceptions as ex
from tickee.paymentproviders.models import PaymentProviderInformation
from tickee.users.manager import lookup_user_by_email

blogger = logging.getLogger("blm.payment")

Session = sqlahelper.get_session()

# Asynchronous Tasks

# Synchronous Tasks

def create_payment_provider(account, psp_data_dict, psp_name):
    """Creates a new payment provider information object"""
    psp_info = PaymentProviderInformation()
    psp_info.account_id = account.id
    psp_info.provider_info = psp_data_dict
    psp_info.provider_type = psp_name
    Session.add(psp_info)
    Session.flush()
    return psp_info

def fetch_checkout_information(order_key):
    """
    Returns the information necessary to perform a payment for the order.
    """
    order = lookup_order_by_key(order_key)
    psp = lookup_payment_provider_for_order(order.id)
    return psp.checkout_transaction(order.id)

def fetch_transaction_status(order):
    """Retrieves the transaction status from the
    payment provider."""
    # find payment provider
    psp = lookup_payment_provider_for_order(order.id)
    # retrieve status & information
    status = psp.transaction_status(order)
    userinfo = psp.transaction_information(order)
    # update user with information from paymet provider
    update_user_information(order, userinfo)
    return status

def update_user_information(order, userinfo):
    """
    Updates the user connected to the order with information retrieved
    from the payment provider.
    """
    user = order.user
    if userinfo.first_name and not user.first_name:
        user.first_name = userinfo.first_name
    if userinfo.last_name and not user.last_name:
        user.last_name = userinfo.last_name
    Session.flush()    
    
    
    try:
        found_user = lookup_user_by_email(userinfo.email)
    except ex.UserNotFoundError:
        # user's email can be updated
        user.meta['secondary_mail'] = user.email
        user.email = userinfo.email
    else:
        # email address already matches or another user with mail adress exists
        # TODO: figure out merging strategy
        return