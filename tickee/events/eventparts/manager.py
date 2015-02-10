from tickee.db.models.eventpart import EventPart
import sqlahelper
import tickee.exceptions as ex

Session = sqlahelper.get_session()

def lookup_eventpart_by_id(eventpart_id):
    """
    Find an ``EventPart`` with a given id.
    
    Args:
        eventpart_id:
            Id of the eventpart
            
    Returns:
        ``EventPart`` object with the given eventpart_id
        
    Raises:
        EventPartNotFoundError        
    """
    eventpart = Session.query(EventPart).get(eventpart_id)
    if not eventpart:
        raise ex.EventPartNotFoundError(eventpart_id, "Could not find the event.")
    return eventpart