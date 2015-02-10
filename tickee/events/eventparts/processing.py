from tickee.db.models.eventpart import EventPart
from tickee.db.models.tickettype import TicketTypeEventPartAssociation
from tickee.events.manager import lookup_event_by_id
from tickee.venues.manager import lookup_venue_by_id
import logging
import sqlahelper

blogger = logging.getLogger('blm.events')

Session = sqlahelper.get_session()

def delete_eventpart(eventpart):
    """ Removes the eventpart from the database """
    # remove eventpart
    blogger.debug('delete eventpart %s' % eventpart.id)
    Session.delete(eventpart)


def add_eventpart(event_id, name=None, 
                  start_datetime=None, end_datetime=None, 
                  venue_id=None):
    """
    Adds an ``EventPart`` to the ``Event`` and returns the id.
    
    Args:
        event_id:
            Id of the ``Event`` where the eventpart will be added
        name:
            Name of the eventpart, e.g. "Day 1", "Marquee"
        start_datetime:
            Date and time when the eventpart will start
        end_datetime:
            Date and time when the eventpart will end
        venue_id:
            Id of the ``Venue`` where the eventpart is held
            
    Returns:
        The newly created ``EventPart``
        
    Raises:
        EventNotFoundError
        VenueNotFoundError
    """
    # check if event exists
    lookup_event_by_id(event_id)
    # optionally check if venue exists
    if venue_id:
        lookup_venue_by_id(venue_id)
    # create event part
    eventpart = EventPart(start_datetime, end_datetime, venue_id)
    eventpart.name = name
    Session.add(eventpart)
    # connect event part to event
    eventpart.event_id = event_id
    Session.flush()
    return eventpart