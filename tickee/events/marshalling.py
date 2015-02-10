from tickee.accounts.marshalling import account_to_dict
from tickee.core.marshalling import date
from tickee.events.eventparts.marshalling import eventpart_to_dict
from tickee.tickettypes import states
from tickee.tickettypes.marshalling import tickettype_to_dict
from tickee.subscriptions.permissions import has_available_transactions



def event_to_dict(event, language='en', 
                         include_visitors=False, 
                         include_tickettypes=False,
                         include_eventparts=False,
                         include_description=True,
                         include_handling_fee=False,
                         include_dates=True,
                         include_account=True):
    """ Converts an ``Event`` object into a dictionary representation. """
    result = dict(id=event.id,
                  name=event.name,
                  image_url=event.image_url,
                  url=event.url,
                  email=event.email)
    # status
    result['active'] = event.is_active
    result['public'] = event.is_public
    
    # Availability
    if has_available_transactions(event.account):
        result['availability'] = event.get_availability()
    else:
        result['availability'] = states.SOLD
        
    if include_handling_fee:
        result['currency'] = event.get_currency()
        result['handling_fee'] = event.get_handling_fee() / 100.00
    if include_description:
        result['description'] = event.get_description(language)
    if include_account:
        result['account'] = account_to_dict(event.account)
    if include_dates:
        result['dates'] = map(date, event.get_dates())
    if include_visitors:
        result['visitors'] = []
    if include_tickettypes:
        result['tickettypes'] = map(lambda tt: tickettype_to_dict(tt, include_availability=True), 
                                    event.get_ticket_types())
    if include_eventparts:
        result['eventparts'] = map(lambda ep: eventpart_to_dict(ep, short=False),
                                   event.parts)
    # Social
    try:
        result['social'] = event.meta['social']
    except:
        result['social'] = None
    
    return result


def event_to_dict2(event, short=False):
    
    result = dict(id=event.id,
                  name=event.name)
    
    if not short:
        result['currency'] = event.get_currency()
        result['handling_fee'] = event.get_handling_fee() / 100.00
        result['dates'] = map(date, event.get_dates())
        result['availability'] = event.get_availability()
        result['active'] = event.is_active
        result['description'] = event.get_description()
        result['image_url'] = event.image_url
        result['url'] = event.url
        result['email'] = event.email
        result['public'] = event.is_public

    return result