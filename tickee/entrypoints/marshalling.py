# -*- coding: utf-8 -*-

from tickee.tickettypes.manager import get_venues_of_tickettype, get_event_of_tickettype
from tickee.tickettypes.states import CLAIMED, SOLD
import datetime
import logging
import tickee.logic as logic
import time

tlogger = logging.getLogger('technical')

def account_to_dict(account):
    """ Converts an ``Account`` object into a dictionary representation. """
    result = dict(id=account.id,
                  name=account.name,
                  email=account.email)
    return result


def event_to_dict(event, language='en', 
                         include_visitors=False, 
                         include_tickettypes=False,
                         include_eventparts=False,
                         include_dates=True,
                         include_account=True):
    """ Converts an ``Event`` object into a dictionary representation. """
    result = dict(id=event.id,
                  name=event.name,
                  description=event.get_description(language),
                  image_url=event.image_url,
                  url=event.url,
                  email=event.email)
    # TODO: include a list of visitors
    if include_account:
        result['account'] = account_to_dict(event.account)
    if include_dates:
        result['dates'] = map(date, event.get_dates())
    if include_visitors:
        result['visitors'] = []
    if include_tickettypes:
        result['tickettypes'] = map(lambda tt: tickettype_to_dict(tt, include_sold_state=True), 
                                    event.get_ticket_types())
    if include_eventparts:
        result['eventparts'] = map(lambda ep: eventpart_to_dict(ep, include_tickettypes=False),
                                   event.parts)
    return result


def eventpart_to_dict(eventpart, include_tickettypes=False):
    result = dict(id=eventpart.id,
                  name=eventpart.name,
                  starts_on=date(eventpart.starts_on),
                  ends_on=date(eventpart.ends_on),
                  venue=eventpart.venue_id,
                  description=eventpart.description)
    if include_tickettypes:
        result['tickettypes'] = map(lambda tt: tickettype_to_dict(tt, include_sold_state=True), 
                                    eventpart.get_ticket_types())
    return result


def venue_to_dict(venue, include_address=False):
    """
    Transform a ``Venue`` object into a dictionary
    """
    result = dict(id=venue.id,
                  name=venue.name,
                  city=venue.address.city)
    # add latlng if available
    if venue.latlng:
        result['latlng'] = venue.latlng
    # add address if requested and available
    if include_address and venue.address:
        result['address'] = address_to_dict(venue.address)
        
    return result
    

def address_to_dict(address):
    """
    Transform a ``Address`` object into a dictionary
    """
    return dict(street_line1=address.street_line1,
                street_line2=address.street_line2,
                postal_code=address.postal_code,
                city=address.city,
                country=address.country)


def tickettype_to_dict(tickettype, 
                       include_availability=False,
                       include_sold_state=False):
    """
    Transform a ``TicketType`` object into a dictionary.
    """
    result = dict(id=tickettype.id,
                  name=tickettype.name,
                  description=tickettype.description,
                  price=float(tickettype.price)/100.00,
                  currency=tickettype.currency_id)
    if include_availability:
        result['available'] = tickettype.amount_available_tickets()
    if include_sold_state:
        result['sold_out'] = (tickettype.availability in [CLAIMED, SOLD])
    return result


def user_to_dict(user, include_name=True):
    """
    Transforms a ``User`` object into a dictionary.
    """
    result = dict(id=user.id)
    if include_name:
        result['first_name'] = user.first_name
        result['last_name'] = user.last_name
    return result


def client_to_dict(client, include_credentials=False, include_scopes=True):
    """
    Transforms a ``OAuth2Client`` object into a dictionary.
    """
    result = dict(id=client.id,
                  name=client.name)
    if include_scopes:
        result['scope'] = client.allowed_scopes
    if include_credentials:
        result['key'] = client.key
        result['secret'] = client.secret
    return result


def ticketorder_to_dict(ticketorder):
    """
    Transforms a ``TicketOrder`` object into a dictionary.
    """
    result = dict(name=ticketorder.ticket_type.name,
                  amount=ticketorder.amount)
    return result


def order_to_dict(order, include_ordered_tickets=False, include_total=False):
    """
    Transforms an ``Order`` object into a dictionary.
    """
    result = dict(key=order.order_key)
    if include_ordered_tickets:
        sub_orders = map(ticketorder_to_dict, order.get_ticketorders())
        result['ordered_tickets'] = sub_orders
    if include_total:
        result['total'] = order.get_total()
    return result


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
                  created_at=timestamp(ticket.created_at))
    if include_user:
        user_info = user_to_dict(ticket.user)
        result['user'] = user_info
    if include_event:
        event = get_event_of_tickettype(ticket.ticket_order.ticket_type)
        result['event'] = dict(id=event.id,
                               name=event.name,
                               start_date=date(event.get_start_date()))
    if include_scanned:
        result['checked_in'] = ticket.is_scanned()
    if include_tickettype:
        result['tickettype'] = tickettype_to_dict(ticket.ticket_order.ticket_type, 
                                                  include_availability=False, 
                                                  include_sold_state=False)
    if include_venues:
        result['venues'] = map(venue_to_dict, 
                               get_venues_of_tickettype(ticket.ticket_order.ticket_type))
    return result


def date(datetime_obj):
    if datetime_obj:
        return datetime_obj.strftime("%Y-%m-%dT%H:%M:%S")
    else:
        return None

def timestamp(datetime_obj):
    if datetime_obj:
        return int(time.mktime(datetime_obj.timetuple()))
    else:
        return None

def error(tickeeerror):
    """
    Default approach to generating error messages.
    """
    result = dict(error=tickeeerror.error())
    return result

def internal_error(exception):
    """
    An internal exception has occurred.
    """
    tlogger.exception(exception)
    return dict(error="An unknown error has occurred.")

created_success_dict = dict(created=True)
created_failed_dict = dict(created=False)
updated_success_dict = dict(updated=True)
updated_failed_dict = dict(updated=False)
purchase_success_dict = dict(purchased=True)
not_implemented_dict = dict(not_implemented=True)