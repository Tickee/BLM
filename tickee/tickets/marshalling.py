from tickee.core.marshalling import timestamp, date
from tickee.tickettypes.manager import get_event_of_tickettype, get_venues_of_tickettype
from tickee.tickettypes.marshalling import tickettype_to_dict
from tickee.users.marshalling import user_to_dict
from tickee.venues.marshalling import venue_to_dict
from tickee.events.marshalling import event_to_dict2


def ticket_to_dict(ticket, 
                   include_scanned=False, 
                   include_user=True,
                   include_event=True,
                   include_tickettype=False,
                   include_venues=False):
    """
    Transforms a ``Ticket``object into a dictionary.
    """
    result = dict(id=ticket.get_code(),
                  created_at=timestamp(ticket.created_at),
                  order_id=ticket.ticket_order.order.id)
    if include_user:
        name = "%s %s" % (ticket.user.first_name or "None", ticket.user.last_name or "None")
        result['user'] = dict(name=name,
                              id=ticket.user.id)
    if include_event:
        event = get_event_of_tickettype(ticket.ticket_order.ticket_type)
        result['event'] = dict(id=event.id,
                               name=event.name,
                               start_date=date(event.get_start_date()))

    result['checked_in'] = ticket.is_scanned()
    if include_tickettype:
        result['tickettype'] = tickettype_to_dict(ticket.ticket_order.ticket_type, 
                                                  include_availability=False)
    if include_venues:
        result['venues'] = map(venue_to_dict, 
                               get_venues_of_tickettype(ticket.ticket_order.ticket_type))
    return result


def ticket_to_dict2(ticket, fields=["id", "user", "creation", "event"]):
    result = dict()
    for field in fields:
        if field == "id":
            result['id'] = ticket.get_code()
        if field == "creation":
            result['created_at'] = timestamp(ticket.created_at)
        if field == "event":
            result['event'] = event_to_dict2(get_event_of_tickettype(ticket.ticket_order.ticket_type),
                                             short=True)
        if field == "user":
            result['user'] = user_to_dict(ticket.user)
    return result