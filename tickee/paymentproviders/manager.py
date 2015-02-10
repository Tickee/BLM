from tickee.accounts.manager import lookup_account_by_id
from tickee.orders.manager import lookup_order_by_id
from tickee.paymentproviders.models import PaymentProviderInformation
from tickee.paymentproviders.providers import PAYMENT_PROVIDERS
import logging
import sqlahelper
import tickee.exceptions as ex

Session = sqlahelper.get_session()

blogger = logging.getLogger('blm.payment')

def lookup_payment_provider_info_by_id(psp_id):
    """
    Returns the payment provider with the id.
    """
    psp = Session.query(PaymentProviderInformation).get(psp_id)
    if not psp:
        raise ex.OrderError("psp_id %s not found" % psp_id)
    return psp


def lookup_payment_provider_class_by_name(psp_name):
    klass = PAYMENT_PROVIDERS.get(psp_name)
    if klass is None:
        raise ex.PaymentError("No payment provider found with that name.")
    return klass


def lookup_payment_provider(account_id):
    """
    Returns the payment provider used for this account.
    """
    account = lookup_account_by_id(account_id)
    if account.paymentproviders:
        for psp in account.paymentproviders:
            if psp.provider_info.get('account_id') and psp.provider_type is not None:
                print psp.id
                klass = PAYMENT_PROVIDERS[psp.provider_type]
                return klass(psp)
    return None    
    
def lookup_payment_provider_for_order(order_id):
    """
    Returns the payment provider handling the order.
    """
    order = lookup_order_by_id(order_id)
    payment_providerinfo = order.payment_provider
    if payment_providerinfo:
        klass = PAYMENT_PROVIDERS.get(payment_providerinfo.provider_type)
        return klass(payment_providerinfo)
    else:
        blogger.error("order %s does not have a payment provider connected" % order_id)
        raise ex.NoAttachedPaymentProviderError