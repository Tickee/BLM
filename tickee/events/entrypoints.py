from celery.task import task
from tickee.accounts.manager import lookup_account_by_id, lookup_account_by_name
from tickee.accounts.permissions import require_account_owner
from tickee.core import entrypoint
from tickee.core.security.oauth2.manager import lookup_account_for_client
from tickee.events import defaults
from tickee.events.defaults import EVENT_NAME
from tickee.events.eventparts.processing import add_eventpart
from tickee.events.manager import lookup_event_by_id, find_events
from tickee.events.marshalling import event_to_dict, event_to_dict2
from tickee.events.permissions import require_event_owner
from tickee.events.processing import start_event, delete_event
from tickee.tickets.manager import list_tickets
from tickee.tickets.marshalling import ticket_to_dict
from tickee.tickettypes.defaults import TICKETTYPE_PRICE, TICKETTYPE_AMOUNT
from tickee.tickettypes.processing import create_tickettype, \
    link_tickettype_to_event
import datetime
import time


@task(name="events.delete")
@entrypoint()
def event_delete(client_id, event_id):
    """ Deletes an eventpart """
    event = lookup_event_by_id(event_id)
    delete_event(event)

@task
@entrypoint()
def event_create(client_id, account_short, event_info, eventparts=[]):
    """
    Entrypoint for creating an event and returning its information back as a
    dictionary.
    
    Args:
        client_id
            The id of the oauth_client who will organize the event. The event 
            will be created for the account owning this client.
        account_short
        event_info
        eventparts
    """
    account = lookup_account_by_name(account_short)
    
    if client_id is not None:
        require_account_owner(client_id, account)
    
    event = start_event(account.id, 
                        event_info.get('name') or EVENT_NAME)
    
    # create default eventpart
    if len(eventparts) == 0:
        add_eventpart(event.id,
                      name=event.name)
    
    # add eventparts as described
    else:
        for eventpart in eventparts:
            if eventpart.get('starts_on') is not None:
                starts_on = datetime.datetime.fromtimestamp(eventpart.get('starts_on'))
            else:
                starts_on = defaults.EVENTPART_START
            minutes = eventpart.get('minutes')
            if starts_on is not None and minutes is not None:
                ends_on = None #starts_on + datetime.timedelta(minutes=minutes)
            else:
                ends_on = None
            
            add_eventpart(event_id=event.id, 
                          name=eventpart.get('name'), 
                          start_datetime=starts_on, 
                          end_datetime=ends_on, 
                          venue_id=eventpart.get('venue'))
    
    # create ticket types
    tickettypes = event_info.get('tickettypes') or []
    for tickettype_info in tickettypes:
        # convert sales_end from ts to datetime
        if tickettype_info.get('sales_end') is not None:
            tickettype_info['sales_end'] = datetime.datetime.utcfromtimestamp(tickettype_info.get('sales_end'))
        # create ticket type
        tt = create_tickettype(price=tickettype_info.get('price') or TICKETTYPE_PRICE, 
                               units=tickettype_info.get('units') or TICKETTYPE_AMOUNT, 
                               currency=tickettype_info.get('currency') or "EUR", 
                               name=tickettype_info.get('name'), 
                               sales_end=tickettype_info.get('sales_end'))
        
        # link it to the event
        link_tickettype_to_event(tt, event)
    
    
    return event_to_dict2(event, short=False)



@task
@entrypoint()
def event_list(client_id=None, account_id=None, account_shortname=None,
               after_date=None, before_date=None,
               limit=50, past=False, active_only=True, public_only=True):
    """
    Entrypoint for finding events matching specific filters.
    
    Args:
        account_id|account_shortname
            Only events owned by this account
        after_date
            Only events that start after this date will be returned
        before_date
            Only events that start before this date will be returned
        limit
            Only return at most this number of events. Defaults to 10.
        past
            Show events that occurred in the past. Defaults to True.
    """
    
    if account_id is not None:
        account = lookup_account_by_id(account_id)
    elif account_shortname is not None:
        account = lookup_account_by_name(account_shortname)
    
    try:
        account_id = account.id
    except:
        account_id = None	
    
    if client_id is not None:
        own_account = lookup_account_for_client(client_id)
        if not own_account == account:
            active_only = True # force active_only when not querying own account   
        
    event_list = find_events(account_id_filter=account_id,
                             after_date_filter=after_date,
                             before_date_filter=before_date,
                             limit=limit,
                             past=past,
                             active_only=active_only,
                             public_only=public_only)
        
    return map(event_to_dict2, event_list)



@task
@entrypoint()
def event_details(client_id, event_id, 
                  include_visitors=False, include_eventparts=False):
    """
    Entrypoint for showing the details of an event.
    
    Args:
        event_id
            The id of the event to show
        include_visitors
            Show all visitors of the event
    """
    event = lookup_event_by_id(int(event_id))
    result = event_to_dict(event, 
                           include_visitors=include_visitors, 
                           include_tickettypes=True,
                           include_handling_fee=True,
                           include_eventparts=include_eventparts)
    return result


@task(name="events.update")
@entrypoint()
def event_update(client_id, event_id, event_info):
    """
    Entrypoint for updating event information.
    
    Args:
        event_id:
            Id of the event to update
        values_dict:
            Dictionary containing information that requires updating. The 
            dictionary can contain the following information:
                -  active: Boolean for turning the event active or inactive.
    
    Returns:
        A dictionary containing a key "updated" which is True if the update
        was completed successfully and False if not. 
        
        {'updated': True}
        
        Even if nothing was updated, it will return True as a value to 
        indicate there were no problems encountered.
    """    
    # check if activation is required
    if client_id:
        require_event_owner(client_id, event_id)
    event = lookup_event_by_id(event_id)
    
    for (key, value) in event_info.iteritems():
        if value is None:
            continue # skip unset fields
        elif key == "active":
            if value:
                event.publish()
            else:
                event.unpublish()
        elif key == "public":
            event.is_public = value  
        elif key == "name":
            event.name = value
        elif key == "url":
            event.url = value
        elif key == "description":
            event.set_description(value.get('text'), value.get('language'))
        elif key == "image_url":
            event.image_url = value
        elif key == "email":
            event.email = value
        elif key == "social":
            event.meta['social'] = value
            
    return event_to_dict(event)
    
    
@task
@entrypoint()
def event_tickets(client_id, event_id, 
                  eventpart_id=None, tickettype_id=None, location_id=None, # filters
                  include_scan_state=False, include_user=False):

    if client_id is not None:
        require_event_owner(client_id, event_id)
        
    tickets = list_tickets(event_id=event_id, 
                           eventpart_id=eventpart_id, 
                           tickettype_id=tickettype_id)
    
    result = dict()
    result['tickets'] = map(lambda t: ticket_to_dict(t, include_scanned=include_scan_state,
                                                        include_user=include_user), 
                            tickets)
    result['timestamp'] = int(time.time())
    return result