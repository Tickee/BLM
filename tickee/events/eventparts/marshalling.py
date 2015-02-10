from tickee.core.marshalling import timestamp


def eventpart_to_dict(eventpart, short=False):
    
    result = dict(id=eventpart.id,
                  name=eventpart.name)
    
    if not short:
        result['starts_on'] = timestamp(eventpart.starts_on)
        result['ends_on'] = timestamp(eventpart.ends_on)
        result['venue_id'] = eventpart.venue_id
        result['description'] = eventpart.get_description()

    return result