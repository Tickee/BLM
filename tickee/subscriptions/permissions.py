from tickee.exceptions import SubscriptionError
from tickee.paymentproviders.processing import get_or_create_transaction_statistic

def has_available_transactions(account):
    """Returns True if the account has not exceeded the number of payed
    transactions allowed this month"""
    statistics = get_or_create_transaction_statistic(account)
    transactions_allowed = account.subscription.get_feature('transactions_per_month')
    return transactions_allowed is None or statistics.amount < transactions_allowed


def require_available_transactions(account):
    """Raises an exception if the account has exceeded the number of payed
    transactions allowed for this month"""
    if not has_available_transactions(account):
        raise SubscriptionError('transaction amount for this month has been reached')