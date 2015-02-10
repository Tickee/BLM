from tickee.accounts.marshalling import account_to_dict, account_to_dict2
from tickee.events.marshalling import event_to_dict, event_to_dict2
from tickee.users.marshalling import user_to_dict

def ticketorder_to_dict(ticketorder):
    """
    Transforms a ``TicketOrder`` object into a dictionary.
    """
    result = dict(name=ticketorder.ticket_type.name,
                  id=ticketorder.ticket_type.id,
                  price=ticketorder.ticket_type.price/100.00,
                  amount=ticketorder.amount)
    return result


def order_to_shortdict(order):
    return order_to_dict(order, short=True)

def order_to_dict(order, include_ordered_tickets=False, include_total=False,
                         include_redirect_url=False, short=False):
    """ Transforms an ``Order`` object into a dictionary. """
    result = dict(key=order.order_key,
                  account=order.account_id)
    if order.user_id is not None:
        result['user'] = order.user_id
        result['guest'] = order.meta.get('gifted')
        result['paper'] = order.meta.get('paper')
    if include_redirect_url:
        result['redirect_url'] = order.meta.get('redirect_url')
    if include_ordered_tickets:
        sub_orders = map(ticketorder_to_dict, order.get_ticketorders())
        sub_orders.append(dict(name="Handling fee",
                               amount=order.get_handling_fee() / 100.00))
        result['tickets_overview'] = sub_orders
    if include_total:
        try:
            currency = order.payment_provider.get_info('currency')
        except:
            currency = "EUR" # TODO: find correct default
        result['total'] = dict(price=order.get_total(),
                               currency=currency)
    return result


def order_to_dict2(order, fields=["overview", "account"]):
    result = dict()
    for field in fields:
        if field == "overview":
            ticketorders_per_event = order.get_ticketorders_per_event()
            events = []
            for event, ticketorders in ticketorders_per_event.iteritems():
                event_info = event_to_dict2(event)
                event_info["tickettypes"] = map(ticketorder_to_dict, ticketorders) 
                events.append(event_info)
            result['events'] = events
        
        elif field == "account":
            result['account'] = account_to_dict2(order.account, fields=["id", "short_name", "name"])
            
        elif field == "user":
            result['user'] = user_to_dict(order.user)
            
        elif field == "key":
            result['key'] = order.order_key
        
        elif field == "total":
            result['total'] = dict(amount=order.get_total() / 100.0,
                                   currency=None) # Todo: find currency of order
        
        elif field == "events":
            result['events'] = map(lambda e: event_to_dict2(e, short=True), 
                                   order.get_events())
            
            
    return result