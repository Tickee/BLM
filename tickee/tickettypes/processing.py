from tickee.core.currency.manager import lookup_currency_by_iso_code
from tickee.db.models.tickettype import TicketType, \
    TicketTypeEventPartAssociation
from tickee.orders.manager import has_orders_for_tickettype
import logging
import sqlahelper
import tickee.exceptions as ex

Session = sqlahelper.get_session()

blogger = logging.getLogger('blm.tickettypes')


def delete_tickettype(tickettype):
    """ Handles deletion of a tickettype by removing the associations to eventparts and
    finally deletes the tickettype itself. """
    # fail if orders for ticket type exist
    if has_orders_for_tickettype(tickettype):
        raise ex.TickeeError("Tickettypes with orders connected to it can't be deleted. Try deactivating it instead.")
    # delete all connections of tickettype to eventpart
    for assoc in tickettype.assocs:
        Session.delete(assoc)
    # delete tickettype
    blogger.debug('delete tickettype %s' % tickettype.id)
    Session.delete(tickettype)


def create_tickettype(price, units, currency="EUR",
                      name="Ticket", description=None, 
                      min_units_order=1, max_units_order=None, sales_start=None, sales_end=None):
    """Creates a new tickettype for an eventpart
    
    Raises:
        InvalidPriceError
            if the price is less than zero
        InvalidAmountError
            if the amount of tickets to sell is less than zero
        CurrencyNotFoundError
            if the currency does not exist
    """
    # price must not be less than zero
    if price < 0:
        raise ex.InvalidPriceError("The price must be 0 or more.")
    # units must not be less than zero
    if units < 0:
        raise ex.InvalidAmountError("The amount of tickets must be 0 or more")
    # check if tickettype exists
    lookup_currency_by_iso_code(currency)
    # create ticket type
    ticket_type = TicketType(name, price, currency, units)
    ticket_type.set_description(description)
    ticket_type.min_units_order = min_units_order
    ticket_type.max_units_order = max_units_order
    ticket_type.sales_start = sales_start
    ticket_type.sales_end = sales_end
    Session.add(ticket_type)
    Session.flush()
    return ticket_type

def link_tickettype_to_eventpart(tickettype, eventpart):
    """Links a tickettype to an eventpart"""
    assoc = TicketTypeEventPartAssociation()
    blogger.info("Linking tickettype %s to eventpart %s" % (tickettype.id, eventpart.id))
    assoc.tickettype = tickettype
    assoc.eventpart_id = eventpart.id
    eventpart.tickettypes.append(assoc)
    
def link_tickettype_to_event(tickettype, event):
    """Links a tickettype to all eventparts of an event"""
    for eventpart in event.parts:
        link_tickettype_to_eventpart(tickettype, eventpart)