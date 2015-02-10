from tickee.subscriptions.models import Subscription
import sqlahelper
from tickee.exceptions import SubscriptionError


Session = sqlahelper.get_session()

def lookup_subscription_by_reference(subscription_ref):
    """ Looks up a subscription using its reference """
    sub = Session.query(Subscription).filter(Subscription.subscription_reference==subscription_ref).first()
    if sub is None:
        raise SubscriptionError('could not find any subscription with reference %s' % subscription_ref)
    return sub