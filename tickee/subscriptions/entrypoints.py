from celery.task import task
from tickee.accounts.manager import lookup_account_by_name, lookup_account_by_id
from tickee.core import entrypoint
from tickee.exceptions import SubscriptionError
from tickee.subscriptions.manager import lookup_subscription_by_reference
from tickee.subscriptions.plans import SAASY_SUBSCRIPTION_MAPPING, FreeSubscriptionPlan
from tickee.subscriptions.processing import fetch_subscription_details
import logging

tlogger = logging.getLogger('technical')

@task(name="subscriptions.notification")
@entrypoint()
def receive_notification(subscription_ref):
    """Receives a Saasy notification and queries the api for the subscription details. 
    
    When it is a brand new subscription, the only way to link it to an account is via 
    its referrer. When the subscription reference is linked, it will also be possible 
    to find the correct account via its subscription reference.
    """
    subscription_details = fetch_subscription_details(subscription_ref)
    
    
    # find internal subscription matching the reference
    try:
        subscription = lookup_subscription_by_reference(subscription_ref)
    except SubscriptionError:
        # find account matching referrer
        try:
            shortname = subscription_details.find('referrer').text
            account = lookup_account_by_name(shortname)
        # no match found, panic!
        except:
            tlogger.exception("Could not find any account associated with subscription %s"\
                              % subscription_ref)
            raise SubscriptionError('Could not associate saasy subscription to an account.')
        else:
            subscription = account.subscription
            subscription.subscription_reference = subscription_ref # link it to saasy subscription        
    
    
    status = subscription_details.find('status').text
    # subscription is active
    if status == "active":
        product_name = subscription_details.find('productName').text
        customer_url = subscription_details.find('customerUrl').text
        plan = SAASY_SUBSCRIPTION_MAPPING.get(product_name)
        # fail if no plan matching the saasy product found
        if plan is None:
            tlogger.error('received subscription (ref %s) with unknown saasy product %s' % (subscription_ref, 
                                                                                            product_name))
            raise SubscriptionError('Unknown product in saasy subscription found.')
            
        # update subscription
        subscription.subscription_type = plan.internal
        subscription.meta['customer_url'] = customer_url
        return dict()
        
    # subscription has inactive status -> revert to freemium
    elif status == "inactive":
        subscription.subscription_type = FreeSubscriptionPlan.internal
        subscription.meta['customer_url'] = None
        
        
    # unknown status
    else:
        tlogger.error("unknown subscription status '%s' for ref %s" % (status, subscription_ref))
