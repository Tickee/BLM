from celery.task import task
from tickee.core import entrypoint
from tickee.events import defaults
from tickee.events.eventparts.manager import lookup_eventpart_by_id
from tickee.events.eventparts.marshalling import eventpart_to_dict
from tickee.events.eventparts.processing import add_eventpart, delete_eventpart
from tickee.events.manager import lookup_event_by_id
from tickee.events.marshalling import event_to_dict
from tickee.events.permissions import require_event_owner, \
    require_eventpart_owner
from tickee.venues.manager import lookup_venue_by_id
import datetime
from tickee.orders.manager import has_orders_for_tickettype
import tickee.exceptions as ex

@task(name="eventparts.delete")
@entrypoint()
def eventparts_delete(client_id, eventpart_id):
    """ Deletes an eventpart """
    eventpart = lookup_eventpart_by_id(eventpart_id)
    delete_eventpart(eventpart)
    
    

@task(name="eventparts.from_event")
@entrypoint()
def eventpart_list(client_id, event_id):
    """Returns a list of all eventparts of the event"""
    event = lookup_event_by_id(event_id)
    if client_id is not None:
        require_event_owner(client_id, event_id)
    return map(lambda ep: eventpart_to_dict(ep, short=True), event.parts)


@task(name="eventparts.details")
@entrypoint()
def eventpart_details(client_id, eventpart_id):
    """Returns information of the eventpart"""
    eventpart = lookup_eventpart_by_id(eventpart_id)
    if client_id is not None:
        require_eventpart_owner(client_id, eventpart_id)
    return eventpart_to_dict(eventpart)


@task(name="eventparts.update")
@entrypoint()
def eventpart_update(client_id, eventpart_id, eventpart_info):
    """
    Entrypoint for updating eventpart information.
    
    Args:
        eventpart_id:
            Id of the event to update
        eventpart_info:
            Dictionary containing information that requires updating. The 
            dictionary can contain the following information:
                - name: name identifying the eventpart
                - starts_on: utc timestamp when the eventpart starts
                - minutes: number of minutes until the eventpart ends
                - venue_id: id of the venue object
                - description: localization dictionary to specify a text and its language
    """    
    # check if activation is required
    if client_id:
        require_eventpart_owner(client_id, eventpart_id)
        
    eventpart = lookup_eventpart_by_id(eventpart_id)
    
    for (key, value) in eventpart_info.iteritems():
        if value is None:
            continue # skip unset fields
        elif key == "name":
            eventpart.name = value
        elif key == "starts_on":
            eventpart.starts_on = datetime.datetime.fromtimestamp(value)
        elif key == "minutes":
            minutes = datetime.timedelta(minutes=value)
            # add minutes to starts_on if available
            if eventpart_info.get('starts_on') is not None:
                eventpart.ends_on = datetime.datetime.fromtimestamp(eventpart_info.get('starts_on'))\
                                    + minutes  
            # extend existing starts_on time
            else:
                eventpart.ends_on = eventpart.starts_on + minutes
        elif key == "venue_id":
            lookup_venue_by_id(value)
            eventpart.venue_id = value
        elif key == "description":
            eventpart.set_description(value.get('text'), value.get('language'))
            
    return eventpart_to_dict(eventpart)


@task(name="eventparts.create")
@entrypoint()
def eventpart_create(client_id, event_id, eventpart_info):
    """Adds an eventpart to the event"""
    
    if client_id is not None:
        require_event_owner(client_id, event_id)
    
    lookup_event_by_id(event_id)
    
    starts_on = datetime.datetime.utcfromtimestamp(eventpart_info.get('starts_on') or defaults.EVENTPART_START)
    minutes = eventpart_info.get('minutes') or defaults.EVENTPART_MINUTES
    ends_on = starts_on + datetime.timedelta(minutes=minutes)
    venue_id = eventpart_info.get('venue_id')
    description = eventpart_info.get('description')
    
    if venue_id is not None:
        lookup_venue_by_id(venue_id)
    
    eventpart = add_eventpart(event_id, 
                              eventpart_info.get('name'), 
                              starts_on, 
                              ends_on, 
                              venue_id)
    if description is not None:
        eventpart.set_description(description.get('text'), description.get('language'))

    return eventpart_to_dict(eventpart)