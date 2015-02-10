from celery.task import task
from tickee.accounts.manager import lookup_account_by_name
from tickee.core import entrypoint
from tickee.core.security.oauth2.manager import lookup_account_for_client
from tickee.db.models.account import Account
from tickee.db.models.eventpart import EventPart
from tickee.db.models.order import Order
from tickee.db.models.ticketorder import TicketOrder
from tickee.db.models.tickettype import TicketType,\
    TicketTypeEventPartAssociation
from tickee.db.models.user import User
from tickee.events.manager import lookup_event_by_id
from tickee.events.permissions import require_event_owner
from tickee.scanning.manager import list_ticketscans
from tickee.tickets.manager import lookup_ticket_by_code, list_tickets
from tickee.tickets.marshalling import ticket_to_dict
from tickee.tickets.models import Ticket
from tickee.tickets.permissions import require_tickettype_owner
from tickee.tickets.processing import delete_ticket
from tickee.tickets.tasks import mail_ticket
from tickee.users.manager import lookup_user_by_id
from tickee.users.marshalling import user_to_dict
import datetime
import sqlahelper

Session = sqlahelper.get_session()

@task(name="tickets.delete")
@entrypoint()
def ticket_delete(client_id, ticket_code):
    """ Deletes a ticket """
    ticket = lookup_ticket_by_code(ticket_code)
    delete_ticket(ticket)


@task(name="tickets.update")
@entrypoint()
def ticket_update(ticket_code, ticket_info):
    """Updates a ticket, supports the following updates:
        - user changes
     """
    user_id = ticket_info.get('user_id')
     
    ticket = lookup_ticket_by_code(ticket_code)
    user = lookup_user_by_id(user_id)
    ticket.user_id = user.id
    
    return ticket_to_dict(ticket)


@task
@entrypoint()
def ticket_details(client_id, ticket_code):
    """Retrieves ticket details"""
    ticket = lookup_ticket_by_code(ticket_code)

    if client_id is not None:
        require_tickettype_owner(client_id, ticket.get_tickettype().id)

    return ticket_to_dict(ticket, include_scanned=True, 
                                      include_user=True,
                                      include_tickettype=True,
                                      include_venues=True)


@task(name="tickets.visitors_of_account")
@entrypoint()
def visitors_of_account(account_short):
    """ Returns a list of users who have attended the events of an account """
    account = lookup_account_by_name(account_short)
    users = Session.query(User).join(Ticket, TicketOrder, Order, Account)\
                   .filter(Account.id == account.id)\
                   .distinct(User.id).all()
    return map(user_to_dict, users)


@task(name="tickets.visitors_of_event")
@entrypoint()
def visitors_of_event(event_id):
    """ Returns a list of users who have attended the events of an account """
    event = lookup_event_by_id(event_id)
    users = Session.query(User).join(Ticket, TicketOrder, TicketType, TicketTypeEventPartAssociation, EventPart)\
                   .filter(EventPart.event_id == event.id)\
                   .distinct(User.id).all()
    return map(user_to_dict, set(users))


@task(name="tickets.resend")
@entrypoint()
def resend(client_id, ticket_code):
    """ Sends a mail containing the ticket to the owner """
    ticket = lookup_ticket_by_code(ticket_code)
    result = mail_ticket(ticket.id)
    return result



@task(name="tickets.from_event")
@entrypoint()
def from_event(client_id, event_id, since=None, ttype=None):
    """ Lists all tickets of an event or show updates if since specified. """ 
    if client_id is not None:
        require_event_owner(client_id, event_id)
        
    # show all tickets
    if since is None:
        tickets = list_tickets(event_id, None, None, ttype)
    
    # show updates since a given timestamp
    else:
        since_datetime = datetime.datetime.utcfromtimestamp(float(since))
        # add updated tickets
        tickets = map(lambda ts: ts.ticket, list_ticketscans(event_id=event_id,
                                                              scanned_after=since_datetime))
        # add new tickets
        tickets += list_tickets(event_id=event_id, purchased_after=since_datetime)
        return map(ticket_to_dict, set(tickets))
    
    return map(lambda t: ticket_to_dict(t, include_scanned=True, include_event=False),
               tickets)
        
        
@task(name="tickets.from_user")
@entrypoint()
def from_user(client_id, user_id, include_failed=False):
    """ Lists all tickets of a user. 
    If client_id is None, all tickets will be returned. Otherwise only tickets
    related to that account will be shown. """
    user = lookup_user_by_id(user_id)
    
    tickets = user.tickets
    
    if client_id is not None:
        account = lookup_account_for_client(client_id)
        tickets = tickets.join("ticket_order", "order", "account").filter(Account.id == account.id)
    
    return map(ticket_to_dict, tickets.all())