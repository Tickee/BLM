from celery.task import task
from tickee.accounts.manager import lookup_account_by_name
from tickee.core import marshalling, entrypoint
from tickee.core.security.oauth2.manager import lookup_account_for_client
from tickee.db.models.eventpart import EventPart
from tickee.db.models.order import Order
from tickee.db.models.ticketorder import TicketOrder
from tickee.db.models.tickettype import TicketTypeEventPartAssociation, \
    TicketType
from tickee.orders import states
from tickee.orders.manager import lookup_order_by_key, lookup_order_by_id
from tickee.orders.marshalling import order_to_dict, ticketorder_to_dict, \
    order_to_dict2, order_to_shortdict
from tickee.orders.processing import start_order, add_tickets, finish_order, \
    delete_order
from tickee.orders.states import PURCHASED
from tickee.orders.tasks import timeout_sessions, mail_order
from tickee.paymentproviders.entrypoints import \
    checkout_order as payment_checkout
from tickee.tickets.marshalling import ticket_to_dict
from tickee.tickets.permissions import require_tickettype_owner
from tickee.users.manager import lookup_user_by_id
from tickee.users.marshalling import user_to_dict
import logging
import sqlahelper
import tickee.exceptions as ex
import tickee.orders.manager as om

blogger = logging.getLogger("blm.entry")
tlogger = logging.getLogger("technical")

Session = sqlahelper.get_session()


@task(name="orders.delete")
@entrypoint()
def order_delete(client_id, order_key):
    """ Deletes the order """
    order = lookup_order_by_key(order_key)
    delete_order(order)


@task(name="orders.list")
@entrypoint()
def order_list(client_id, order_id=None):
    """ Sends a mail containing the ticket to the owner """
    if order_id is not None:
        try:
            order = lookup_order_by_id(order_id)
        except ex.OrderNotFoundError:
            return []
        else:
            details = dict(id = order.id,
                          status = order.status,
                          user = user_to_dict(order.user),
                          account = dict(id = order.account_id,
                                         name = order.account.name),
                          tickets = map(lambda t: ticket_to_dict(t, 
                                                                 include_scanned=True, 
                                                                 include_user=False),
                                      order.get_tickets()),
                          orders = map(lambda to: ticketorder_to_dict(to), order.ordered_tickets))
            return [details]
    return []



@task(name="orders.resend")
@entrypoint()
def resend(client_id, order_key):
    """ Sends a mail containing the ticket to the owner """
    order = lookup_order_by_key(order_key)
    result = mail_order(order.id)
    return result


@task(name="orders.gift")
@entrypoint()
def gift(client_id, order_key, user_id=None):
    """ Skips the payment provider and finishes the order as a gift """
    order = lookup_order_by_key(order_key)
    
    if user_id is not None:
        user = lookup_user_by_id(user_id)
    else:
        user = None
        
    order.checkout(user)
    order.meta['gifted'] = True
    result = order_to_dict(order, include_ordered_tickets=True) 
    finish_order(order, as_guest=True)
    return result


@task(name="orders.paper")
@entrypoint()
def paper(client_id, order_key, user_id ):
    """ Skips the payment provider and finishes the order as a paper ticket """
    order = lookup_order_by_key(order_key)
    
    user = lookup_user_by_id(user_id)
    
    order.checkout(user)
    order.meta['paper'] = True
    result = order_to_dict(order, include_ordered_tickets=True) 
    finish_order(order, send_mail=False)
    return result


@task(name="orders.from_user")
@entrypoint()
def from_user(client_id, user_id, include_failed=False):
    """ Lists all orders of a user """
    user = lookup_user_by_id(user_id)
    
    orders = user.orders
    
    if client_id is not None:
        account = lookup_account_for_client(client_id)
        orders = orders.filter_by(account_id=account.id)
    
    if not include_failed:
        orders = orders.filter(Order.status==states.PURCHASED)
    
    return map(lambda o: order_to_dict2(o, fields=['account', 'key', 'events']), 
               orders.all())

@task(name="orders.from_event")
@entrypoint()
def from_event(client_id, event_id):
    """ Lists all orders of an event """
    orders = Session.query(Order).join(TicketOrder,TicketType,TicketTypeEventPartAssociation, EventPart)\
                    .filter(Order.status == states.PURCHASED)\
                    .filter(EventPart.event_id == event_id).all()
    
    return map(order_to_shortdict, orders)


@task(name="orders.from_account")
@entrypoint()
def from_account(client_id, account_id):
    """ Lists all orders of an account """
    orders = Session.query(Order)\
                    .filter(Order.status == states.PURCHASED)\
                    .filter(Order.account_id == account_id).all()
    
    return map(order_to_shortdict, orders)



@task(name="orders.checkout")
@entrypoint()
def order_checkout(client_id, order_key, payment_required=True, redirect_url=None, user_id=None):
    """ Checks out the order """
    order = lookup_order_by_key(order_key)
    if order.meta.get('gifted', False):
        # gift order
        return gift(client_id, order_key, user_id)
    elif order.meta.get('paper', False):
        # paper ticket
        return paper(client_id, order_key, user_id)
    else:
        # use payment provider
        return payment_checkout(client_id, order_key, payment_required, redirect_url, user_id)



@task
@entrypoint()
def order_new(client_id, user_id, tickettype_id, amount, account_short=None, as_guest=False, as_paper=False):
    """
    Starts a new order session or retrieves one that was still active.
    
    Args:
        client_id
        user_id: 
            Id of the user to start a session for.
    """
    timeout_sessions(600)
    
    # assert permission to order tickettype
    if client_id is not None:
        require_tickettype_owner(client_id, tickettype_id)
    
    # get account to create order for.
    if account_short is not None:
        account = lookup_account_by_name(account_short)
    else:
        account = lookup_account_for_client(client_id)
        
    # start an order or get current one.    
    if user_id is not None:
        user = lookup_user_by_id(user_id)
        order = start_order(user, account)
    else:
        order = start_order(None, account)
        
    # set order as guest (optional)
    if as_guest:
        order.meta['gifted'] = True
        
    # set order as paper ticket (optional)
    if as_paper:
        order.meta['paper'] = True
        
    add_tickets(order, tickettype_id, amount)

    # build successful order
    order_info = order_to_dict(order)
    return order_info


@task
@entrypoint()
def order_add(client_id, order_key, tickettype_id, amount, meta=None):
    """
    Adds a request for an amount of tickets to an order.
    
    Args:
        client_id:
            Id of the requesting client
        order_key:
            Key of the order
        tickettype_id:
            Id of the ticket type to order
        amount:
            Amount of units to order.
            
    Returns:
        Dictionary containing an "added" field with stating that the ticket 
        was added to the order as well as an "order_key" used for checkout
        purposes.
    """
    # Security    
    timeout_sessions(600)

    # assert permission to order tickettype
    if client_id is not None:
        require_tickettype_owner(client_id, tickettype_id)
    # TODO: assert account is owner of order

    # add tickets
    order = lookup_order_by_key(order_key)
    add_tickets(order, tickettype_id, amount)
    
    # add meta
    if meta and meta.get('users_allocate'):
        order.meta['users_allocate'] = meta.get('users_allocate')

    order_info = order_to_dict(order)
    return order_info

@task
@entrypoint()
def order_details(client_id, order_key):
    """
    Retrieves order information
    """

    order = om.lookup_order_by_key(order_key)

    if order.user_id is not None:
        user_info = dict(full_name = order.user.get_full_name(),
                         id = order.user.id,
                         user_mail = order.user.email)
    else:
        user_info = None

    result = order_to_dict(order)

    result = dict(id = order.id,
                  status = order.status,
                  user = user_info,
                  account = dict(id = order.account_id,
                                 name = order.account.name),
                  redirect_url = order.meta.get("redirect_url"),
                  tickets = map(lambda t: ticket_to_dict(t, 
                                                        include_scanned=True, 
                                                        include_user=False),
                              order.get_tickets()),
                  orders = map(lambda to: ticketorder_to_dict(to), order.ordered_tickets))
    if order.status == PURCHASED:
        result['purchased_on'] = marshalling.date(order.purchased_on)
    return result


@task(name="orders.started.details")
@entrypoint()
def started_order_details(client_id, order_key):
    """ """
    timeout_sessions()
    order = om.lookup_order_by_key(order_key)
    if order.status == states.STARTED and not order.is_locked():
        return order_to_dict2(order, fields=["overview", "account"])
    else:
        raise ex.OrderNotFoundError()
    
    

@task
@entrypoint()
def order_cancel(payment_key):
    """
    Does nothing.
    
    Args:
        payment_key:
            Payment key of the order
            
    Returns:
        ??
    """
    return