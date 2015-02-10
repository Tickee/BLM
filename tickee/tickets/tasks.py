from celery.task import task
from jinja2.environment import Environment
from jinja2.loaders import PackageLoader
from tickee.core.crm.tasks import log_crm
from tickee.core.mail import send_email
from tickee.core.validators import validate_email
from tickee.tickets.manager import tickets_from_order, get_event_of_ticket, lookup_ticket_by_id
from tickee.tickets.models import Ticket
import logging
import sqlahelper
import tickee.exceptions as ex
import transaction


Session = sqlahelper.get_session()

blogger = logging.getLogger('blm.tickets')
tlogger = logging.getLogger('technical')


@task
def mail_ticket(ticket_id, fake=False):
    """ Sends a ticket to the user. """   
    try:
        ticket = lookup_ticket_by_id(ticket_id)
        event = get_event_of_ticket(ticket)
        order = ticket.ticket_order.order
        
        env = Environment(loader=PackageLoader('tickee', 'templates'),
                          extensions=['jinja2.ext.with_'])
        body = env.get_template('mail_ticket.html')\
                  .render(ticket=ticket, 
                          account=order.account,
                          event=event, 
                          order=order, 
                          as_guest=False)
        
        body_plain = env.get_template('mail_ticket.txt')\
                        .render(ticket=ticket, 
                                account=order.account,
                                event=event, 
                                order=order, 
                                as_guest=False)
        
        # send generated mail
        blogger.info('sending mail for ticket %s to user %s (%s)' % (ticket.id, 
                                                                     ticket.user.id, 
                                                                     ticket.user.email))
        
        validate_email(ticket.user.email)
        
        if not ticket.user.email:
            raise ex.OrderError("user has no email.")
               
        if not fake:
            send_email("Tickee Ticketing <tickets@tick.ee>", 
                       ticket.user.email, 
                       "Your ticket for '%s' is here!" % event.name, 
                       body,
                       body_plain)
        
        log_crm("ticket", ticket.id, dict(action="mailed",
                                          addressee=ticket.user.email))
        transaction.commit()
        return True
        
        
    except Exception as e:
        try:
            email = ticket.user.email
        except:
            email = "no mail found."
        log_crm("ticket", ticket_id, dict(action="mail failed",
                                          addressee=email))
        transaction.commit()
        tlogger.exception("failed sending mail for ticket %s: %s" % (ticket_id, e))
        return False





def create_tickets(order):
    """Creates tickets for an order."""
    if has_created_tickets(order):
        return # no need to create tickets
    
    if order.meta.get('users_allocate'):
        multi_users = order.meta.get('users_allocate')
        multi_users = multi_users.get('ids')
        multi_users.insert(0, order.user_id)
    else:
        multi_users = None
    
    amount = 0
    for ticketorder in order.get_ticketorders():
        for i in range(ticketorder.amount):
            if multi_users and multi_users[amount] :
                ticket = Ticket(ticketorder.id, multi_users[amount])
            else :
                ticket = Ticket(ticketorder.id, order.user_id)
            ticketorder.tickets.append(ticket)
            Session.flush()
            blogger.info("created ticket %s, code %s." % (ticket.id, ticket.get_code()))
            amount += 1
    
    log_crm("order", order.id, dict(action="created tickets",
                                    amount=amount))
    return amount

def has_created_tickets(order):
    """Checks if tickets have already been created"""
    return len(tickets_from_order(order)) > 0