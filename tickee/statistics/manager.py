from tickee.db.models.order import PURCHASED, Order
from tickee.orders.manager import get_order_query



def get_ticketorders_per_date(event_id, allowed_states=[PURCHASED]):
    """
    Returns the number of of tickets sold for given period
    """
    orders = get_order_query(event_id, allowed_states).order_by(Order.purchased_on)
    
    sales = dict()
    for order in orders:
        if order.purchased_on:
            date = order.purchased_on.date()
        else:
            date = order.session_start.date()
        sales[date] = sales.get(date, 0) + order.get_ticket_count()
    return sales