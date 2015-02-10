from tickee.db.models.tickettype import TicketType
import tickee.exceptions as ex
import sqlahelper


Session = sqlahelper.get_session()


def get_availability(tickettype_id):
    """
    Retrieves the availability of the tickettype.
    
    Raises
        TicketTypeNotFoundError
    """
    tickettype = lookup_tickettype_by_id(tickettype_id)
    return tickettype.availability

def get_venues_of_tickettype(tickettype):
    """ Returns all venues where this tickettype is valid """
    eventpart_assocs = tickettype.assocs
    eventparts = map(lambda a: a.eventpart, eventpart_assocs)
    venues = map(lambda ep: ep.venue, eventparts)
    venues = [v for v in venues if v is not None]
    return set(venues)

def get_event_of_tickettype(tickettype):
    """ Returns the event of the tickettype """
    eventpart_assocs = tickettype.assocs
    eventparts = map(lambda a: a.eventpart, eventpart_assocs)
    return eventparts[0].event


def lookup_tickettype_by_id(tickettype_id):
    """
    Looks up a tickettype
    """
    tickettype = Session.query(TicketType).get(tickettype_id)
    if not tickettype:
        raise ex.TicketTypeNotFoundError
    else:
        return tickettype
    
