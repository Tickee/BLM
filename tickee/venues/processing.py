from sqlalchemy.exc import IntegrityError
from tickee.venues.models import Address, Venue
import sqlahelper
import tickee.exceptions as ex


Session = sqlahelper.get_session()

def delete_venue(venue):
    """ Handles deletion of a venue. """
    Session.delete(venue)
    

def create_address(street_line1=None, street_line2=None,
                   postal_code=None, city=None, country_code=None):
    """
    Creates an ``Address`` object.
    
    Args:
        street_line1:
        street_line2:
        postal_code:
        city:
        country:
                
    Returns:
        The newly created ``Address`` object.
    """
    address = Address(street_line1, street_line2, postal_code, 
                      city, country_code)
    Session.add(address)
    Session.flush()
    return address


def create_venue(venue_name):
    """
    Creates a ``Venue`` object.
    
    Args:
        venue_name:
            The name of the venue
            
    Returns:
        The newly created ``Venue`` object.
    """
    # create venue
    venue = Venue(venue_name)
    Session.add(venue)
    try:
        Session.flush()
    except IntegrityError as e:
        raise ex.VenueExistsError
    return venue