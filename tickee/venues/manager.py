from sqlalchemy.sql.expression import func
from tickee.venues.models import Venue
import sqlahelper
import tickee.exceptions as ex

Session = sqlahelper.get_session()


def lookup_venue_by_id(venue_id):
    """
    Looks up a ``Venue`` with a specific id.
    """
    venue = Session.query(Venue).get(venue_id)
    if not venue:
        raise ex.VenueNotFoundError()
    return venue

def lookup_venues_by_name(name_filter=None, limit=10):
    """
    Lookup a ``Venue`` in the database matching a filter.
    """
    venues = Session.query(Venue).order_by(Venue.name)
    if name_filter:
        venues = venues.filter(func.lower(Venue.name).like("%"+name_filter.lower()+"%"))
    return list(venues.limit(limit))

def list_venues(account):
    """ Returns a list of venues of the account """
    venues = Session.query(Venue).filter(Venue.creator==account).all()
    return venues

def list_venues_of_event(event):
    """ Returns a list of all venues connected to an event """
    venues = []
    venues.append(event.venue)
    for eventpart in event.parts:
        venues.append(eventpart.venue)
    venues = [v for v in venues if v is not None]
    return set(venues)
    