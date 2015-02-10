def tickettype_to_dict(tickettype, 
                       include_availability=False):
    """
    Transform a ``TicketType`` object into a dictionary.
    """
    result = dict(id=tickettype.id,
                  name=tickettype.name,
                  description=tickettype.get_description(),
                  price=tickettype.price / 100.00,
                  handling_fee=tickettype.get_handling_fee() / 100.00,
                  active=tickettype.is_active,
                  currency=tickettype.currency_id)
    if include_availability:
        result['availability'] = tickettype.get_availability()
    return result



def tickettype_to_dict2(tickettype, short=False):
    result = dict(id=tickettype.id,
                  name=tickettype.name,
                  price=tickettype.price / 100.0,
                  currency=tickettype.currency_id,
                  amount=tickettype.units,
                  availability=tickettype.get_availability())
    
    if not short:
        result['active'] = tickettype.is_active
        result['description'] = tickettype.get_description()
        result['handling_fee'] = tickettype.get_handling_fee() / 100.0
    return result