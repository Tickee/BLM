from tickee.core.marshalling import date


def ticketscan_to_dict(ticketscan):
    """
    Transforms a ``TicketScan``object into a dictionary.
    """
    result = dict()
    result['id'] = ticketscan.ticket.get_code() 
    result['user_id'] = ticketscan.ticket.user_id
    result['scanned_at'] =  date(ticketscan.scanned_date)
    return result