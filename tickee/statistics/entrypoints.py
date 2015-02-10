from celery.task import task
from tickee.accounts.manager import lookup_account_by_name
from tickee.accounts.permissions import require_account_owner
from tickee.core import entrypoint
from tickee.events.manager import lookup_event_by_id
from tickee.events.permissions import require_event_owner
from tickee.paymentproviders.processing import get_or_create_transaction_statistic
from tickee.statistics.processing import total_tickets, detailed_ticket_count, total_tickets_of_event, \
    total_available_of_event, orders_of_event, total_guest_tickets_of_event


@task
@entrypoint()
def event_statistics(client_id, event_id):
    """Returns a dictionary containing statistics of all purchased orders."""
    event = lookup_event_by_id(event_id)
    
    if client_id is not None:
        require_event_owner(client_id, event_id)
    
    return dict(total_sold=total_tickets_of_event(event),
                total_available=total_available_of_event(event),
                total_orders=orders_of_event(event),
                total_guests=total_guest_tickets_of_event(event))


@task(name="statistics.account")
@entrypoint()
def account_statistics(client_id=None, account_id=None):
    """Returns general account statistics"""
    account = lookup_account_by_name(account_id)
    if client_id is not None:
        require_account_owner(client_id, account)        
    
    transaction_stats = get_or_create_transaction_statistic(account)
    transactions_allowed = account.subscription.get_feature('transactions_per_month') or -1
    return dict(total_sold=total_tickets(account),
                transactions_this_month=transaction_stats.amount,
                transactions_allowed=transactions_allowed)


@task(name="statistics.account.detailed")
@entrypoint()
def account_detailed_statistics(client_id=None, account_id=None, max_months_ago=12):
    """Returns statistics per month"""
    account = lookup_account_by_name(account_id)
    if client_id is not None:
        require_account_owner(client_id, account)
    
    return detailed_ticket_count(account, max_months_ago)
    
    