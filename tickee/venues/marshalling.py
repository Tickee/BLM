def address_to_dict(address):
    """
    Transform a ``Address`` object into a dictionary
    """
    return dict(street_line1=address.street_line1,
                street_line2=address.street_line2,
                postal_code=address.postal_code,
                city=address.city,
                country=address.country)


def venue_to_dict(venue, include_address=False):
    """
    Transform a ``Venue`` object into a dictionary
    """
    result = dict(id=venue.id,
                  name=venue.name)
    if venue.address is not None:
        result['city'] = venue.address.city
    # add latlng if available
    if venue.latlng:
        result['latlng'] = venue.latlng
    # add address if requested and available
    if include_address and venue.address:
        result['address'] = address_to_dict(venue.address)
        
    return result