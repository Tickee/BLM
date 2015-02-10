from tickee.scanning.models import TicketScan
from tickee.tickets.manager import lookup_ticket_by_code
import sqlahelper

Session = sqlahelper.get_session()

def scan_ticket(ticket_code, scan_date, extra_info):
    """
    Scan in a ticket.
    
    Args:
        ticket_code:
            Hex string representing the id of the ticket.
        scan_date:
            Datetime containing the time the ticket was scanned
        extra_info:
            A dictionary containing extra information the account owner
            wishes to have.
            
    Returns:
        The newly created ``TicketScan`` object.
    
    Raises:
        TicketNotFoundError
    """
    # mark ticket as scanned
    ticket = lookup_ticket_by_code(ticket_code)
    scan = TicketScan(scan_date, extra_info)
    scan.ticket_id = ticket.id
    Session.add(scan)
    Session.flush()
    return scan