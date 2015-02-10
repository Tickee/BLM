from celery.task import task
from tickee.core import entrypoint
from tickee.events.eventparts.manager import lookup_eventpart_by_id
from tickee.events.manager import lookup_event_by_id
from tickee.events.permissions import require_event_owner, \
    require_eventpart_owner
from tickee.orders.manager import has_orders_for_tickettype
from tickee.tickets.permissions import require_tickettype_owner
from tickee.tickettypes import defaults
from tickee.tickettypes.manager import lookup_tickettype_by_id
from tickee.tickettypes.marshalling import tickettype_to_dict, \
    tickettype_to_dict2
from tickee.tickettypes.processing import create_tickettype, \
    link_tickettype_to_eventpart, link_tickettype_to_event, delete_tickettype
import datetime
import tickee.exceptions as ex


@task(name="tickettypes.from_event")
@entrypoint()
def from_event(client_id, event_id, include_private=False):
    """ Returns tickettypes connected to the event. By default it only returns public tickettypes """
    if client_id:
        require_event_owner(client_id, event_id)
    event = lookup_event_by_id(event_id)
    
    tickettypes = event.get_ticket_types(include_inactive=include_private,
                                         include_if_sales_finished=include_private)
    
    return map(lambda tt: tickettype_to_dict(tt, include_availability=True), 
               sorted(tickettypes, key=lambda tt: tt.id))


@task(name="tickettypes.from_eventpart")
@entrypoint()
def from_eventpart(client_id, eventpart_id, include_private=False):
    """ Returns tickettypes connected to the eventpart. By default it only returns public tickettypes """
    if client_id:
        require_eventpart_owner(client_id, eventpart_id)
    eventpart = lookup_eventpart_by_id(eventpart_id)
    
    tickettypes = eventpart.get_ticket_types(include_inactive=include_private,
                                             include_if_sales_finished=include_private)
    return map(lambda tt: tickettype_to_dict(tt, include_availability=True), tickettypes)



@task(name="tickettypes.details")
@entrypoint()
def tickettype_details(client_id, tickettype_id):
    """ Returns a tickettype """
    # permission check
    if client_id:
        require_tickettype_owner(client_id, tickettype_id)
    # update tickettype 
    tickettype = lookup_tickettype_by_id(tickettype_id)
       
    return tickettype_to_dict2(tickettype)



@task(name="tickettypes.update")
@entrypoint()
def tickettype_update(client_id, tickettype_id, tickettype_info):
    """ Updates a tickettype """
    # permission check
    if client_id:
        require_tickettype_owner(client_id, tickettype_id)
    # update tickettype
    tickettype = lookup_tickettype_by_id(tickettype_id)
    for (key,value) in tickettype_info.iteritems():
        if value is None:
            continue # skip unset fields
        elif key == "name":
            tickettype.name = value
        elif key == "price":
            tickettype.price = value
        elif key == "units":
            tickettype.units = value
        elif key == "handling_fee":
            tickettype.handling_fee = value
        elif key == "description":
            tickettype.set_description(value.get('text'), value.get('language'))
        elif key == "min_order":
            tickettype.min_order = value
        elif key == "max_order":
            tickettype.max_order = value
        elif key == "sales_start":
            tickettype.sales_start = datetime.datetime.utcfromtimestamp(value)
        elif key == "sales_end":
            tickettype.sales_end = datetime.datetime.utcfromtimestamp(value)
        elif key == "min_order":
            tickettype.min_order = value
        elif key == "max_order":
            tickettype.max_order = value
        elif key == "active":
            if value:
                tickettype.publish()
            else: 
                tickettype.unpublish()
        
    return tickettype_to_dict2(tickettype)

@task(name="tickettypes.delete")
@entrypoint()
def tickettype_delete(client_id, tickettype_id):
    """ Deletes a tickettype ONLY IF no tickets have been purchased from it """
    tickettype = lookup_tickettype_by_id(tickettype_id)
    # remove ticket type
    delete_tickettype(tickettype)


@task(name="tickettypes.create")
@entrypoint()
def tickettype_create(client_id, tickettype_info, event_id=None, eventpart_id=None): 
    """ Creates a tickettype and links it to either an event or eventpart"""
    # Set defaults for missing values
    name = tickettype_info.get('name')
    description = tickettype_info.get('description')
    price = tickettype_info.get('price') or defaults.TICKETTYPE_PRICE
    currency = tickettype_info.get('currency') or defaults.TICKETTYPE_CURRENCY
    units = tickettype_info.get('units') or defaults.TICKETTYPE_AMOUNT
    min_order = tickettype_info.get('minimum_order') or defaults.TICKETTYPE_MIN_ORDER
    max_order = tickettype_info.get('maximum_order') or defaults.TICKETTYPE_MAX_ORDER
    
    sales_start = tickettype_info.get('sales_start')
    sales_end = tickettype_info.get('sales_start')
    
    if event_id is None and eventpart_id is None:
        raise ex.TickeeError("eventpart_id or event_id required.")
    
    # price must not be less than zero
    if price < 0:
        raise ex.InvalidPriceError("The price must be 0 or more.")
    # units must not be less than zero
    if units < 0:
        raise ex.InvalidAmountError("The quantity of tickets must be 0 or more.")
    # minimum order must not be less than zero
    if min_order and min_order < 0:
        raise ex.InvalidAmountError("The minimum order limit must be 1 or more.")
    # maximum order must not be less than minimum order
    if max_order and max_order < min_order:
        raise ex.InvalidAmountError("The maximum order limit must be equal or more than the minimum limit.")
   
    
    # decide on sales start/end times
    if event_id:
        if client_id is not None:
            require_event_owner(client_id, event_id)
        event = lookup_event_by_id(event_id)
        default_sale_start = event.get_start_date()
        default_sale_end = event.get_end_date()
    elif eventpart_id:
        if client_id is not None:
            require_eventpart_owner(client_id, eventpart_id)
        eventpart = lookup_eventpart_by_id(eventpart_id)
        default_sale_start = eventpart.starts_on
        default_sale_end = eventpart.ends_on
    else:
        raise ex.EventPartNotFoundError('Tickettype needs to be connect to either an event or eventpart.')
        
    if sales_start is None:
        sales_start = default_sale_start
    else:
        sales_start = datetime.datetime.utcfromtimestamp(int(sales_start))
        
    if sales_end is None:
        sales_end = default_sale_end
    else:
        sales_end = datetime.datetime.utcfromtimestamp(int(sales_end))
    
    # create ticket type
    tickettype = create_tickettype(price, units, currency, name, 
                                   None, min_order, max_order, 
                                   sales_start, sales_end)
    
    # set description
    if description is not None:
        tickettype.set_description(description.get('text'), description.get('language'))
    
    # link new tickettype to eventpart / event
    if event_id:
        link_tickettype_to_event(tickettype, event)

    elif eventpart_id:
        link_tickettype_to_eventpart(tickettype, eventpart)

    return tickettype_to_dict2(tickettype)