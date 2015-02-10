from tickee.db.models.order import Order
from tickee.db.models.ticketorder import TicketOrder
from tickee.orders.states import STARTED, PURCHASED
import logging
import sqlahelper
import tickee.exceptions as ex

Session = sqlahelper.get_session()

blogger = logging.getLogger("blm.order")
tlogger = logging.getLogger("technical")

def has_orders_for_tickettype(tickettype):
    """ Returns ``True`` if there have been tickets 
    ordered (not specifically purchased) for this tickettype """
    amount_ordered = Session.query(TicketOrder)\
                            .filter(TicketOrder.ticket_type_id==tickettype.id).count()
    return amount_ordered > 0
    
    


def get_started_order(user_id, account_id):
    """
    Finds an active order of a user that is not locked
    """
    order = Session.query(Order).filter(Order.user_id==user_id)\
                                .filter(Order.account_id==account_id)\
                                .filter(Order.locked==False)\
                                .filter(Order.status==STARTED).first()
    if not order:
        raise ex.OrderNotFoundError("User has no active orders for that account.")
    else:
        return order


def get_orders_of_user(user_id):
    """
    Returns all orders created by the user.
    """
    orders = Session.query(Order).filter(Order.user_id==user_id).all()
    return orders
    
def lookup_order_by_id(order_id):
    """
    Finds an order with a given id.
    """
    order = Session.query(Order).get(order_id)
    if not order:
        raise ex.OrderNotFoundError("No order found with id %s" % order_id)
    return order
    
def lookup_order_by_key(order_key):
    """
    Finds a ticket order with a given order_key.
    """
    order = Session.query(Order).filter_by(order_key=order_key).first()
    if not order:
        raise ex.OrderNotFoundError("No order found with order_key %s" % order_key)
    return order


def lookup_order_by_payment_key(payment_key):
    """
    Finds a ticket order with a given payment_key.
    """
    order = Session.query(Order).filter_by(payment_key=payment_key).first()
    if not order:
        raise ex.OrderNotFoundError("No order found with payment_key %s" % payment_key)
    return order

        
def get_order_query(event_id, allowed_states=[PURCHASED]):
    """
    Returns a query of all the orders for an event
    """
    orders = Session.query(Order).filter(Order.status.in_(allowed_states))
    return orders
        