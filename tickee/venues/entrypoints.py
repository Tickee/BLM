from celery.task import task
from tickee.accounts.manager import lookup_account_by_name
from tickee.core import marshalling, entrypoint
from tickee.core.security.oauth2.manager import lookup_account_for_client
from tickee.events.manager import lookup_event_by_id
from tickee.venues.manager import lookup_venue_by_id, lookup_venues_by_name, \
    list_venues, list_venues_of_event
from tickee.venues.marshalling import venue_to_dict
from tickee.venues.processing import create_address, create_venue, delete_venue
import tickee.exceptions as ex


@task(name="venues.from_account")
@entrypoint()
def from_account(client_id, account_name=None):
    """ Returns a list of venues connected to the account"""
    if client_id is not None:
        account = lookup_account_for_client(client_id)
    elif account_name is not None:
        account = lookup_account_by_name(account_name)
    return map(venue_to_dict, list_venues(account))


@task(name="venues.from_event")
@entrypoint()
def from_event(client_id, event_id):
    """ Returns a list of venues connected to an event """
    event = lookup_event_by_id(event_id)
    return map(venue_to_dict, list_venues_of_event(event))  


@task(name="venues.create")
@entrypoint()
def venue_create(client_id, location_info, address_info=None, account_name=None):
    """
    Handles the creation of a ``Venue`` and its ``Address`` and returns 
    the result.
    
    Arguments:
        client_id:
            Name of the OAuth2Client that requested the application.
        location_info:
            Dictionary containing location information:
              - name
        address_info (optional):
            Dictionary containing address information:
              - street_line1, street_line2, postal_code, city, country
        account_name (optional):
            shortname of account that created the location
    """
    # create venue
    if client_id is not None:
        account = lookup_account_for_client(client_id)
    elif account_name is not None:
        account = lookup_account_by_name(account_name)
    else:
        raise ex.VenueError('an account has to be linked to the location')
        
    venue = create_venue(location_info.get('name'))
    venue.created_by = account.id

    # create address if available
    if isinstance(address_info, dict):
        address = create_address(street_line1=address_info.get('street_line1'), 
                                 street_line2=address_info.get('street_line2'), 
                                 postal_code=address_info.get('postal_code'), 
                                 city=address_info.get('city'), 
                                 country_code=address_info.get('country'))
        venue.address = address
    return venue_to_dict(venue, include_address=True)

@task(name="venues.update")
@entrypoint()
def venue_update(client_id, location_id, location_info, address_info=None, account_name=None):
    """
    Updates a venue and returns the new information. It is currently only possible to update
    address information
    
    Arguments:
        client_id:
            Name of the OAuth2Client that requested the application.
        location_id:
            The id of the venue to update.
        location_info:
            Dictionary containing location information.
        address_info (optional):
            Dictionary containing address information:
              - street_line1, street_line2, postal_code, city, country
        account_name (optional):
            shortname of account that created the location
    """
    # create venue
    venue = lookup_venue_by_id(location_id)

    if address_info is not None:
        if venue.address is None:
            venue.address = create_address(street_line1=address_info.get('street_line1'), street_line2=address_info.get('street_line2'), postal_code=address_info.get('postal_code'), city=address_info.get('city'), country_code=address_info.get('country'))
    	else :
            address = venue.address

            for (key, value) in address_info.iteritems():
                if value is None:
                    continue # skip unset fields
                elif key == "street_line1":
                    address.street_line1 = value
                elif key == "street_line2":
                    address.street_line2 = value
                elif key == "postal_code":
                    address.postal_code = value
                elif key == "city":
                    address.city = value
                elif key == "country":
                    address.country = value

    if location_info is not None:
        for (key, value) in location_info.iteritems():
            if value is None:
                continue # skip unset fields
            elif key == "name":
                venue.name = value


    return venue_to_dict(venue, include_address=True)


@task(name="venues.delete")
@entrypoint()
def venue_delete(location_id):
    """ Deletes a venue. If it is linked to an event, 
    that event will lose its venue. """
    venue = lookup_venue_by_id(location_id)
    delete_venue(venue)
    

@task(name="venues.details")
@entrypoint()
def venue_details(location_id, include_address=True):
    """
    Returns information about the requested location.
    
    Args:
        location_id:
            Id of the requested ``Venue`` information
        use_address (optional):
            Should the address be included. Defaults to True.
            
    Returns:
        TODO: documentation
    """
    venue = lookup_venue_by_id(location_id)
    return venue_to_dict(venue, include_address=include_address)


@task(name="venues.search")
@entrypoint()
def venue_search(name_filter, limit=10):
    """
    Searches for ``Venue`` objects.
    
    Args:
        name_filter:
            Show only venues whose name contains this string
        limit (optional):
            Limit the amount of venues. Defaults to 10.
            
    Returns:
        TODO: documentation
    """
    venues = lookup_venues_by_name(name_filter, limit)
    venues_info = map(lambda v: venue_to_dict(v, include_address=True), venues)
    return venues_info