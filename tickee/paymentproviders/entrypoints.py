from celery.task import task
from tickee.accounts.manager import lookup_account_by_name
from tickee.core import marshalling, entrypoint
from tickee.core.security.oauth2.manager import lookup_account_for_client
from tickee.exceptions import PaymentError
from tickee.orders.marshalling import order_to_dict
from tickee.orders.processing import finish_order
from tickee.paymentproviders import states
from tickee.paymentproviders.generic import PaymentProvider
from tickee.paymentproviders.manager import lookup_payment_provider_info_by_id, \
    lookup_payment_provider, lookup_payment_provider_class_by_name
from tickee.paymentproviders.marshalling import psp_to_dict
from tickee.paymentproviders.processing import increment_transaction_count, \
    create_payment_provider_information, validate_payment_provider_information
from tickee.paymentproviders.tasks import update_user_information, \
    create_payment_provider
from tickee.users.manager import lookup_user_by_id
import logging
import sqlahelper
import tickee.exceptions as ex
import tickee.orders.manager as om
import transaction

Session = sqlahelper.get_session()

blogger = logging.getLogger('blm.payment')


@task(name="psp.details")
@entrypoint()
def psp_details(client_id, account_shortname):
    """Returns detailed information about the psp"""
    account = lookup_account_by_name(account_shortname)
    psp = lookup_payment_provider(account.id)
    if psp is not None:
        return psp_to_dict(psp.payment_provider_info)
    else:
        raise PaymentError('Account has no payment provider set up.')

@task(name="psp.update")
@entrypoint()
def psp_update(client_id, account_shortname, psp_name, psp_data):
    """Updates the psp of the account"""
    account = lookup_account_by_name(account_shortname)
    # look for existing psp
    psp = lookup_payment_provider(account.id)
    # psp does not exist -> create
    if psp is None:
        psp_info = create_payment_provider_information(account.id, psp_name, psp_data)
        
    # psp exists -> update
    else:
        psp_info = psp.get_provider_info()
        # update it
        print psp_name
        if psp_name is not None:
            psp_info.provider_type = psp_name
        if psp_data is not None:
            # validate if all mandatory fields are available
            validate_payment_provider_information(psp_info, psp_data)
            for key, new_value in psp_data.iteritems():
                if new_value is None:
                    continue
                else:
                    psp_info.provider_info[key] = new_value
                
    return psp_to_dict(psp_info)



@task
@entrypoint()
def notification(psp_id, context):
    # get the psp
    try:
        provider_info = lookup_payment_provider_info_by_id(psp_id)
        psp = PaymentProvider.build_from_info(provider_info)
    except Exception as e:
        return marshalling.error(e)
    
    # process notification
    try:
        status = psp.handle_notification(context)
        # new order received
        blogger.info('received notification %s (%s) for order %s' % (status,
                                                                     psp.get_name(), 
                                                                     psp.get_order().id))
        if status == states.PSP_NEW_ORDER:
            handle_new_order(psp, context)
        elif status == states.PSP_RISK_ASSESSMENT:
            handle_risk_assessment(psp, context)
        elif status == states.PSP_STATE_CHANGED:
            handle_state_change(psp, context)
        elif status == states.PSP_READY_FOR_PAYMENT:
            handle_ready_for_payment(psp, context)
        elif status == states.PSP_PAYED:
            handle_payed(psp, context)
        elif status == states.PSP_CHARGEBACK_REQUESTED:
            handle_chargeback_requested(psp, context)
        elif status == states.PSP_REFUNDED:
            handle_refunded(psp, context)
        elif status == states.PSP_CANCELLED:
            handle_cancelled(psp, context)
        # something else
        else:
            blogger.error("received unknown status from psp: %s" % status)
        
    except ex.TickeeError as e:
        transaction.abort()
        # let the psp know something went wrong
        return psp.generate_failure_response(context)
    else:
        transaction.commit()
        # let the psp know everything went smooth
        return psp.generate_success_response(context)

def handle_new_order(psp, context):
    """
    The PSP notified that it received a new order.
    """
    pass

def handle_risk_assessment(psp, context):
    """
    The PSP has assessed the risk of the transaction
    """
    pass

def handle_state_change(psp, context):
    """
    The PSP notifies the transaction state has changed
    """
    pass

def handle_ready_for_payment(psp, context):
    """
    The PSP has done all verifications and is now able to charge the 
    customer
    """
    order = psp.get_order()
    psp.charge_order(order)

def handle_payed(psp, context):
    """
    The transaction has been charged and completed.
    """
    order = psp.get_order()
    Session.refresh(order)
    if not order.is_purchased():
        # update user information with new data from payment provider
        update_user_information(order, psp.get_buyer_information())
        # increase transaction counter
        increment_transaction_count(order.account, order.get_ticket_count())
        # create & mail tickets
        finish_order(order, send_mail=True)

def handle_cancelled(psp, context):
    """
    The transaction was cancelled by the payment provider
    """
    pass

def handle_chargeback_requested(psp, context):
    """
    A chargeback request has been initiated
    """
    pass

def handle_refunded(psp, context):
    """
    The money was refunded to the customer.
    """
    pass


@task
def checkout_order(client_id, order_key, payment_required=True, redirect_url=None, user_id=None):
    """
    Checks out the order and returns the redirect url necessary for the payment.
    """
    """
    Locks an order so no other ticket orders can be added to it and links the
    accounts payment provider to it. 
    
    Args:
        order_key:
            Key of the order
        payment_required
            Skips payment provider if set to False, defaults to True
        redirect_url
            URL used by paymentprovider to redirect user after purchase
        user_id
            Allows late-binding of user to the order during checkout phase. Only
            gets bound when the order previously did not have a user connected to it.
            
    Returns:
        The payment information necessary to complete the order.
        
    Raises:
        OrderLockedError
            if the order has already been checked out.
    """
    result = dict()
    
    try:
        order = om.lookup_order_by_key(order_key)
        
        # assure order has not been locked before
        if order.is_locked():
            raise ex.OrderLockedError("the order has already been checked out.")
        
        if user_id is not None:
            user = lookup_user_by_id(user_id)
        else:
            user = None
            
        order.checkout(user)
        order.touch()
        order.meta['redirect_url'] = redirect_url
        
        # payment is necessary when total is not zero and not a gift
        if payment_required and order.get_total() > 0:
            # the organising account has no psp set up
            if len(order.account.paymentproviders) == 0:
                raise ex.PaymentError("the account has no payment provider configured to handle an order.")
            # tickettype has currency allowed by psp
#            order_currency = order.account.paymentproviders[0].get_info("currency")
#            if order_currency != tickettype.currency_id:
#                raise ex.CurrencyError("not allowed to order with this currency.")
            # link payment provider to order
            account = order.account
            psp = lookup_payment_provider(account.id)

#			DEFAULT PSP HACK!
            if psp is None:
                psp = lookup_payment_provider(21)
            
            
            order.payment_provider_id = psp.get_provider_info().id
            payment_info = psp.checkout_order(order)
            if payment_info is None:
                raise ex.PaymentError("received error from payment service provider.")
            result['payment_info'] = payment_info
            result['status'] = order.status
        # no payment necessary, mark as purchased.
        else:
            result['status'] = order.status
            finish_order(order)
        
    except ex.TickeeError as e:
        blogger.error("failed checking out order %s: %s" % (order_key, e))
        transaction.abort()
        return marshalling.error(e)
    
    else:
        order = om.lookup_order_by_key(order_key)
        result['order'] = order_to_dict(order, include_ordered_tickets=True,
                                               include_total=True)
        transaction.commit()
        return result