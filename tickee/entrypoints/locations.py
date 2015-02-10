from celery.task import task
import marshalling
import tickee.exceptions as ex
import tickee.logic as logic
import transaction


@task
def create_location(requestor_id, location_name, latlng=None, address_dict=None,
                    account_id=None):
    """
    Handles the creation of a ``Venue`` and its ``Address`` and returns 
    the result.
    
    Args:
        requestor_id:
            Name of the OAuth2Client that requested the application.
        location_name:
            Name of the location
        latlng (optional):
            Lattitude and longtitude of location
        address_dict (optional)
            Dictionary containing address data.
            Should contain the following keys: 
                street_line1, street_line2, postal_code, city, country
                
    Returns:
        TODO: documentation
    """
    vm = logic.VenueManager()
    sm = logic.SecurityManager()
    # create venue
    try:
        if not account_id:
            account = sm.lookup_account_for_client(requestor_id)
            account_id = account.id
        venue = vm.create_venue(location_name)
        venue.created_by = account_id
    except ex.TickeeError, e:
        transaction.abort()
        return marshalling.error(e)
    else:
        venue_info = marshalling.venue_to_dict(venue)
    # create address if available
    if address_dict:
        try:
            address = vm.create_address(**address_dict)
        except ex.TickeeError, e:
            transaction.abort()
            return marshalling.error(e)
        else:
            venue.address = address
            venue_info = marshalling.venue_to_dict(venue, include_address=True)
            
    transaction.commit()
    # build result
    result = marshalling.created_success_dict.copy()
    result['location'] = venue_info
    return result


@task
def show_location(location_id, use_address=True):
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
    vm = logic.VenueManager()
    try:
        venue = vm.lookup_venue_by_id(location_id)
    except ex.VenueNotFoundError:
        return dict(location=None)
    else:
        return dict(location=marshalling.venue_to_dict(venue, 
                                                       include_address=use_address))


@task
def location_search(name_filter, limit=10):
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
    vm = logic.VenueManager()
    venues = vm.find_venues_by_filter(name_filter, limit)
    venues_info = map(marshalling.venue_to_dict, venues)
    return dict(locations=venues_info)