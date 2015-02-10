from celery.task import task
from tickee.orders.states import PURCHASED
from tickee.tickets.permissions import require_tickettype_owner
import logging
import marshalling
import tickee.exceptions as ex
import tickee.orders.manager as om
import transaction


blogger = logging.getLogger("blm.entry")
tlogger = logging.getLogger("technical")

@task
def start_order_session(user_id, application_key):
    """
    Starts a new order session or retrieves one that was still active.
    
    Args:
        user_id: 
            Id of the user to start a session for.
        application_key:
            Id of the application requesting the information.
    """    
    try:
        # start an order or get current one.
        order = om.start_order(user_id)
    except ex.UserNotFoundError, e:
        blogger.error("Order session failed to start for user %s" % user_id)
        tlogger.error("start_order_session failure: %s" % e)
        transaction.abort()
        # build failed result
        return marshalling.error(e.error())
    else:
        # build successful order
        blogger.info("Order %s created for user %s" % (order.id, user_id))
        order_info = marshalling.order_to_dict(order)
        user_info = marshalling.user_to_dict(order.user)
        transaction.commit()
        return dict(authenticated=True,
                    user=user_info,
                    order=order_info)


@task
def add_to_order(client_id, order_key, user_id, tickettype_id, amount):
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
    om.timeout_sessions(600)
    try:
        # assert permission to order tickettype
        require_tickettype_owner(client_id, tickettype_id)
        # create order if not yet available
        if not order_key:
            order = om.start_order(user_id)
            order_key = order.order_key
        # add tickets to order
        om.add_tickets(order_key, tickettype_id, amount)
    except ex.TickeeError, e:
        transaction.abort()
        return marshalling.error(e)
    else:
        transaction.commit()
        # build result 
        result = dict(added=True, 
                      order_key=order_key)
        return result

@task
def order_info(client_id, order_id):
    """
    Retrieves order information
    """
    try:
        order = om.lookup_order_by_id(order_id)
    except ex.TickeeError as e:
        transaction.abort()
        return marshalling.error(e)
    except Exception as e:
        transaction.abort()
        return marshalling.internal_error(e)
    else:
        result = dict(id=order.id,
                      status=order.status,
                      user=order.user.get_full_name(),
                      user_mail=order.user.email,
                      tickets=map(lambda t: marshalling.ticket_to_dict(t, 
                                                             include_scanned=True, 
                                                             include_user=False),
                                  order.get_tickets()))
        if order.status == PURCHASED:
            result['purchased_on'] = marshalling.date(order.purchased_on)
        return result

@task
def cancel_order(payment_key):
    """
    Does nothing.
    
    Args:
        payment_key:
            Payment key of the order
            
    Returns:
        ??
    """
    return