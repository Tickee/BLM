from celery.task import task
from tickee.events.permissions import require_event_owner
import datetime
import marshalling
import tickee.exceptions as ex
import tickee.logic as logic
import transaction

@task
def create_event(oauth_client_id, event_name, venue_id=None, 
                 price=None, units=None, currency="EUR",
                 account_id=None):
    """
    Entrypoint for creating an event and returning its information back as a
    dictionary.
    
    Args:
        oauth_client_id
            The id of the oauth_client who will organize the event. The event 
            will be created for the account owning this client.
        event_name
            The name of the event
        venue_id
            The id of the venue object where this event will be held
        price
            Ticket price
        units
            Amount of tickets to be sold
        currency
            Currency of the price
            
    Returns:
        A dictionary containing the information of the newly created event
        including its identifier. A ``created`` key-value pair is added 
        indicating the success of the attempt. For example:
        
        {'created': True,
         'event': {"id": 42, 
                   "name": "Tickee Event"}
        }
         
        The dictionary will only contain the created key if the attempt was not
        successful:
        
        {'created': False}
    """
    em = logic.EventManager()
    tm = logic.TicketManager()
    sm = logic.SecurityManager()
    # create event
    try:
        if account_id is None:
            account = sm.lookup_account_for_client(oauth_client_id)
            account_id = account.id
        event = em.start_event(account_id, event_name)
        # add default eventpart
        event.venue_id = venue_id
        eventpart = em.add_eventpart(event.id, venue_id=venue_id)
        # add default ticket type
        tm.create_ticket_type(eventpart.id, price, units, currency=currency)
    except ex.TickeeError, e:
        transaction.abort()
        return marshalling.error(e)
    else:
        result = marshalling.created_success_dict.copy()
        result['event'] = marshalling.event_to_dict(event)
        transaction.commit()
        return result

@task
def list_events(account_id=None, 
                after_date=None, 
                before_date=None,
                limit=10,
                past=True):
    """
    Entrypoint for finding events matching specific filters.
    
    Args:
        account_id
            Only events owned by this account
        after_date
            Only events that start after this date will be returned
        before_date
            Only events that start before this date will be returned
        limit
            Only return at most this number of events. Defaults to 10.
        past
            Show events that occurred in the past. Defaults to True.
            
    Returns:
        A dictionary containing a list of events. For example:
        
        {'events': [{"id": 42, "name": "Tickee Event"}, .. ]}
         
        The dictionary will contain an empty list if no events found:
        
        {'events': []}
    """
    em = logic.EventManager()
    event_list = em.find_events(account_id_filter=account_id,
                                after_date_filter=after_date,
                                before_date_filter=before_date,
                                limit=limit,
                                past=past)
    result = dict(events=map(marshalling.event_to_dict, event_list))
    return result
        
@task
def show_event(event_id, include_visitors=False):
    """
    Entrypoint for showing the details of an event.
    
    Args:
        event_id
            The id of the event to show
        include_visitors
            Show all visitors of the event
            
    Returns:
        A dictionary containing event information and if required a list
        of users that purchased tickets for the event. For example:
        
        {'event': {"id": 42, 
                   "name": "Tickee Event",
                   "visitors": [{"first_name": "Kevin",
                                 "last_name": "Van Wilder"}, .. ],
                   "tickettypes": [
                       {"id": 1,
                        "name": "Ticket Name",
                        "description": "Ticket description",
                        "price": 100.00,
                        "sold_out": False}
                   ]
        }}
         
        The dictionary will contain a null event if no event found:
        
        {'event': null}
    """
    em = logic.EventManager()
    try:
        print type(event_id)
        event = em.lookup_event_by_id(int(event_id))
    except ex.EventNotFoundError:
        transaction.abort()
        return dict(event=None)
    else:
        result = dict(event=marshalling.event_to_dict(event, 
                                                      include_visitors=include_visitors, 
                                                      include_tickettypes=True))
        transaction.commit()
        return result

@task
def update_event(client_id, event_id, values_dict):
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
    em = logic.EventManager()
    # check if activation is required
    try:
        require_event_owner(client_id, event_id)
        if values_dict.get('active'):
            # also activate all ticket_types connected to it.
            event = em.lookup_event_by_id(event_id)
            event.publish()
    except ex.TickeeError, e:
        transaction.abort()
        return marshalling.error(e)
    else:
        transaction.commit()
        return marshalling.updated_success_dict
    