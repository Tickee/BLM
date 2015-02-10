from tickee.db.models.event import Event
from tickee.db.models.eventpart import EventPart
import datetime
import sqlahelper
import tickee.exceptions as ex

Session = sqlahelper.get_session()

def lookup_event_by_id(event_id):
    """
    Find an ``Event`` with a given id.
    
    Args:
        event_id:
            Id of the event
    
    Returns:
        ``Event`` object with the given event_id
    
    Raises:
        EventNotFoundError
    """
    event = Session.query(Event).get(event_id)
    if not event:
        raise ex.EventNotFoundError(event_id, "Could not find the event.")
    return event


def find_events(account_id_filter=None,
                after_date_filter=None, before_date_filter=None,
                limit=None, past=None, active_only=True, public_only=True):
    """
    Retrieves a list of all events matching the specified criteria:
        -  The event owner matches the account_id_filter
        
    Args:
        account_id_filter (optional):
            Show only events owned by this account
        after_date_filter (optional):
            Show only events that start after a date and time
        before_date_filter (optional):
            Show only events that start before a date and time
        limit (optional):
            Limit the amount of events to this amount
        past (optional):
            Show events in the past. Relative to 
            ``datetime.datetime.utcnow()``.
    
    Returns:
        List of ``Event`` objects matching the criteria.
    """
    events = Session.query(Event)
    # filter by account
    if account_id_filter:
        events = events.filter(Event.account_id==account_id_filter)
    # filter by active state
    if active_only:
        events = events.filter(Event.is_active==True)
    # filter by visiblity
    if public_only:
        events = events.filter(Event.is_public==True)
    # TODO: filter by after_date
    # TODO: filter by before date
    # TODO: filter past
    if not past:
        events = events.join(EventPart).filter(EventPart.ends_on >= datetime.datetime.utcnow())
    # limit
    if limit:
        events = events.limit(limit)
    # sort events per start_date    
    return sorted(events.all(), key=lambda event:event.get_start_date())
