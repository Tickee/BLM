# -- database representation for subscription model ---------------------------

FREE = 0
PREMIUM = 1
PREMIUMPRO = 2

# -- abstract subscription plan -----------------------------------------------

class SubscriptionPlan(object):
    """Base subscription model defining defaults for a subscription plan.
    The disabling of specific features is handled in the concrete subscription
    plan."""
    transactions_per_month = None
    service_fee_enabled = True        

# -- concrete subscription plan -----------------------------------------------

class FreeSubscriptionPlan(SubscriptionPlan):
    """Restricted plan for free use."""
    internal = FREE
    transactions_per_month = 500
    service_fee_enabled = False


class PremiumSubscriptionPlan(SubscriptionPlan):
    """Payed plan allowing more features than free plan."""
    internal = PREMIUM
    transactions_per_month = 2500


class PremiumProSubscriptionPlan(SubscriptionPlan):
    """Top of the line plan allowing all features."""
    internal = PREMIUMPRO

# -- Saasy name to subscription plan mapping ----------------------------------

SAASY_SUBSCRIPTION_MAPPING = {
    "Premium": PremiumSubscriptionPlan,
    "PremiumPro": PremiumProSubscriptionPlan
}