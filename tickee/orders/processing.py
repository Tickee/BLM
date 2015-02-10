from tickee.core.crm.tasks import log_crm
from tickee.db.models.order import Order
from tickee.db.models.ticketorder import TicketOrder
from tickee.orders.manager import get_started_order, lookup_order_by_id
from tickee.orders.states import PURCHASED
from tickee.orders.tasks import mail_order
from tickee.subscriptions.permissions import has_available_transactions
from tickee.tickets.manager import tickets_from_order
from tickee.tickets.processing import delete_ticket
from tickee.tickets.tasks import create_tickets
from tickee.tickettypes.manager import lookup_tickettype_by_id
from tickee.tickettypes.tasks import update_availability
import datetime
import logging
import sqlahelper
import tickee.exceptions as ex
import transaction

blogger = logging.getLogger('blm.orders')

Session = sqlahelper.get_session()

def delete_order(order):
    """ Removes a complete order, including tickets """
    # remove ticket
    for ticket in tickets_from_order(order):
        delete_ticket(ticket)
    # remove ticket order
    for ticketorder in order.ordered_tickets:
        Session.delete(ticketorder)
    # finally remove order
    Session.delete(order)



def start_order(user, account):
    """
    Starts an order session for a user and returns the order key. If an 
    order for this user already exists, return that one.
    
    Args:
        user:
            Id of the purchasing user. If user is None, it will be required to
            bind it to a user at checkout.
        account:
            The order is for purchasing from this account
            
    Returns:
        The newly created ``Order`` object
    
    Raises:
        UserNotFoundError
    """
    if user is not None:
        # return existing order if possible
        try:
            started_order = get_started_order(user.id, account.id)
        except ex.OrderNotFoundError:
            # create new order if not possible
            return new_order(user, account)
        else:
            blogger.info("existing order %s found for user %s and account %s" % (started_order.id, user.id, account.id))
            return started_order
    else:
        # create a new order that is not yet bound to a user
        return new_order(None, account)
    

def new_order(user, account):
    """ Creates a new order between a user and an account """
    if user is not None:
        order = Order(user.id, account.id)
    else:
        order = Order(None, account.id)
    Session.add(order)
    Session.flush()
    if user is not None:
        blogger.debug("order %s created for user %s and account %s" % (order.id, user.id, account.id))
    else:
        blogger.debug("order %s created for unknown user and account %s" % (order.id, account.id))
    return order


def add_tickets(order, tickettype_id, amount):
    """
    Will update the order to include the new amount for a tickettype.
    A pre-existing ticketorder for that tickettype will be updated, else
    a new ticketorder will be created.
    
    The following conditions have to be met:
        -  the order has not been locked or confirmed for purchase
        -  the amount is more than 0
        -  there exists a ticket_type matching the id
        -  the ``TicketType`` is set to active
        -  there are still enough tickets available
        -  the ``TicketType`` is owned by the account connected to the order
        
    When tickets are added to an order, the availabilty of the TicketType
    might change from AVAILABLE to CLAIMED
    
    Raises:
        InvalidAmountError
        OrderLockedError
        TicketTypeNotFoundError
        InactiveTicketTypeError
        AmountNotAvailableError
    """
    # valid amount check
    if amount < 0:
        blogger.debug('failed adding invalid amount %s to order %s' % (amount, order.id))
        raise ex.InvalidAmountError("You must purchase at least one ticket.")
    # order is not locked
    if order.is_locked() or order.status == PURCHASED:
        blogger.debug('failed adding to locked order %s' % order.id)
        raise ex.OrderLockedError("No other tickets can be added to this order.")
    # tickettype exists
    tickettype = lookup_tickettype_by_id(tickettype_id)
    # active tickettype check
    if not tickettype.is_active:
        blogger.debug('failed adding inactive tickettype %s to order %s' % (tickettype_id, order.id))
        raise ex.InactiveTicketTypeError("The ticket type is not active.")
    # tickettype is connected to an event
    if tickettype.get_event() is None:
        raise ex.EventNotFoundError("The tickettype is not connected to any event.")
    # tickettype is owned by account connected to the order
    if order.account != tickettype.get_event().account:
        raise ex.AccountError("only orders for tickettypes of account %s possible" % order.account.id)
    # there are still transactions available for the account or it is a free tickettype.
    if not (has_available_transactions(order.account) or tickettype.is_free()):
        raise ex.SubscriptionError("account has reached maximum allowed transactions.")
    
    ticketorder = order.ordered_tickets.filter(TicketOrder.ticket_type_id==tickettype_id).first()
    
    # creates new ticketorder if none found
    if not ticketorder:
        # check if ticketorder contains one or more tickets
        if amount <= 0:
            raise ex.AmountNotAvailableError('at least 1 ticket required')
        # check if tickettype still has enough available
        if not order.meta.get('gifted', False) and not order.meta.get('paper', False) and not tickettype.has_available(amount):
            blogger.info('failed to add unavailable amount %s of tickettype %s to order %s'\
                          % (amount, tickettype_id, order.id))
            raise ex.AmountNotAvailableError("Not enough tickets available.")
        ticketorder = TicketOrder(order.id, tickettype_id, amount)
        blogger.info('created ticketorder for order %s (%sx tickettype %s)'\
                     % (order.id, amount, tickettype_id))
        log_crm("order", order.id, dict(action="add",
                                        tickettype_id=tickettype_id,
                                        amount=amount))
        Session.add(ticketorder)
    
    # updates amount of existing one
    else:
        if amount == 0:
            # remove ticketorder if amount is 0
            Session.delete(ticketorder)
        else:
            # check if additional amount is still available
            additional_tickets = amount - ticketorder.amount
            if not order.meta.get('gifted', False) and additional_tickets >= 0 and not tickettype.has_available(additional_tickets):
                blogger.debug('failed to add unavailable amount %s of tickettype %s to order %s'\
                              % (amount, tickettype_id, order.id))
                raise ex.AmountNotAvailableError("Not enough tickets available.")
            ticketorder.amount = amount
        
        # report update
        blogger.info('updated ticketorder %s for order %s (%sx tickettype %s)'\
                     % (ticketorder.id, order.id, amount, tickettype_id))
        log_crm("order", order.id, dict(action="update",
                                        tickettype_id=tickettype_id,
                                        amount=amount))
    order.touch()
    update_availability.delay(tickettype.id)
    Session.flush()
    


def finish_order(order, send_mail=True, as_guest=False):
    """
    Finish the order by creating the tickets and optionally sending them to the user.
    Unlocked orders can not be purchased.
    """
    try:
        order_id = order.id
        # mark order as purchased
        order.purchase()
        # handle ticket creation
        create_tickets(order)
        order.meta['tickets_created'] = datetime.datetime.utcnow().strftime("%d-%m-%Y %H:%M:%S UTC%z")
        transaction.commit()
        # send mail if requested
        if send_mail:
            mail_order.delay(order_id, as_guest=as_guest, auto_retry=True)
        # update tickettype availability in orders
        order = lookup_order_by_id(order_id)
        for tickettype in order.get_ticket_types():
            update_availability.delay(tickettype.id)
    except Exception as e:
        blogger.exception("failed finalizing order %s" % order_id)
        raise e