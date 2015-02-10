from sqlalchemy.sql.expression import func, extract
from sqlalchemy.sql.functions import count
from tickee.db.models.event import Event
from tickee.db.models.eventpart import EventPart
from tickee.db.models.order import Order
from tickee.db.models.ticketorder import TicketOrder
from tickee.db.models.tickettype import TicketTypeEventPartAssociation, TicketType
from tickee.orders import states
from tickee.orders.marshalling import order_to_shortdict
from tickee.tickets.models import Ticket
from tickee.tickettypes.marshalling import tickettype_to_dict
import datetime
import sqlahelper


Session = sqlahelper.get_session()


# -- Events -------------------------------------------------------------------

def total_tickets_of_event(event):
    """ Returns the total number of tickets sold of the event """
    tickets = Session.query(Ticket.id).distinct(Ticket.id).join(TicketOrder, TicketType, TicketTypeEventPartAssociation, EventPart)\
                     .filter(EventPart.event_id==event.id).count()
    return tickets

def total_available_of_event(event):
    """ Returns the total amount of tickets available for this event """
    tickettypes = event.get_ticket_types(include_if_sales_finished=True)
    total = 0
    for tt in tickettypes:
        total += tt.units
    return total

def sold_per_tickettype_of_event(event):
    """ Returns a dictionary containing statistics on how many units were sold 
    per tickettype """
    tickettypes = Session.query(TicketType).join(TicketTypeEventPartAssociation, EventPart)\
                         .filter(EventPart.event_id==event.id).all()
    return map(lambda tt: tickettype_to_dict(tt), tickettypes)

def orders_of_event(event):
    """ Returns the total amount of purchased orders of the event """
    order_amount = Session.query(Order).join(TicketOrder, TicketType, TicketTypeEventPartAssociation, EventPart)\
                          .distinct(Order.id)\
                          .filter(EventPart.event_id == event.id)\
                          .filter(Order.status == states.PURCHASED).count()
    return order_amount
    
def guest_orders_of_event(event):
    """ Returns the amount of guest orders of this event.
    TODO: META FILTER WON'T WORK. """
    order_amount = Session.query(Order).join(TicketOrder, TicketType, TicketTypeEventPartAssociation, EventPart)\
                          .distinct(Order.id)\
                          .filter(EventPart.event_id == event.id)\
                          .filter(Order.meta.like('%g%'))\
                          .filter(Order.status == states.PURCHASED).count() # TODO: Order.meta.like() is a hack
    return order_amount

def total_guest_tickets_of_event(event):
    """ Calculates the amount of guest tickets of an event """                        
    ticket_and_order = Session.query(Ticket.id, Order.meta, Order.id).distinct(Ticket.id)\
                              .join(TicketOrder, Order, TicketType, TicketTypeEventPartAssociation, EventPart)\
                              .filter(EventPart.event_id == event.id)\
                              .filter(Order.status == states.PURCHASED)
    count = 0 
    for ticket_id,order_meta,order_id in ticket_and_order:
        if "gifted" in order_meta:
            count += 1
            
    return count


# -- Accounts -----------------------------------------------------------------

def total_tickets(account, year=None, month=None):
    """ Returns the total number of tickets sold by the account. """
    tickets = Session.query(Ticket.id)
    # filter by year
    if year is not None:
        tickets = tickets.filter(extract('year', Ticket.created_at)==year)
    # filter by month
    if month is not None:
        tickets = tickets.filter(extract('month', Ticket.created_at)==month)
    tickets = tickets.join(TicketOrder, Order).filter(Order.account_id==account.id)
    return tickets.count()


def detailed_ticket_count(account, max_months_ago=None):
    """ Returns a thing """
    tickets = Session.query(func.date_part('year', Ticket.created_at),
                            func.date_part('month', Ticket.created_at),
                            count(Ticket.id))\
                     .join(TicketOrder, Order).filter(Order.account_id==account.id)\
                     .group_by(func.date_part('year', Ticket.created_at),
                               func.date_part('month', Ticket.created_at))
                     
    if max_months_ago is not None:
        past_date = datetime.datetime.utcnow() - datetime.timedelta(days=(max_months_ago*365)/12)
        past_date = datetime.date(year=past_date.year, month=past_date.month, day=1) # set to beginning of month
        tickets = tickets.filter(Ticket.created_at >= past_date)
    
    statistic_tuples = tickets.all() # [[year, month, amount], ..]
    result = dict()
    for year, month, amount in statistic_tuples:
        year = int(year)
        month = int(month)
        amount = int(amount)
        if year in result:
            if not month in result[year]:
                result[year][month] = amount
            else:
                result[year][month] += amount
        else:
            result[year] = {month: amount}
    return result