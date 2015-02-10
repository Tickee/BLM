# -*- coding: utf-8 -*-

from celery.task import task
from jinja2.environment import Environment
from jinja2.loaders import PackageLoader
from tickee.core.crm.tasks import log_crm
from tickee.core.mail import send_email
from tickee.core.validators import validate_email
from tickee.db.models.order import Order
from tickee.orders.states import STARTED
from tickee.tickettypes.tasks import update_availability
import datetime
import logging
import sqlahelper
import tickee.exceptions as ex
import tickee.orders.manager as om
import transaction

blogger = logging.getLogger('blm.orders')
tlogger = logging.getLogger('technical')

Session = sqlahelper.get_session()

# Asynchronous Tasks

@task(default_retry_delay=60)
def mail_order(order_id, fake=False, as_guest=False, auto_retry=False):
    """
    Sends the mail of the order to the user.
    """
    # fetch information for template
    try:
        order = om.lookup_order_by_id(order_id)
        
        # generate template
        env = Environment(loader=PackageLoader('tickee', 'templates'),
                          extensions=['jinja2.ext.with_'])
        
        validate_email(order.user.email)
        
        if not order.user.email:
            raise ex.OrderError("user has no email.")
        
        if len(order.get_tickets()) == 0:
            raise ex.TicketError("no tickets found.")
        
        # send out a mail per event
        tickets_per_event = order.get_tickets_per_event()
        for event in tickets_per_event:
            tickets = tickets_per_event[event]
                    
            # send generated mail
            blogger.info('sending mail for "order %s - event %s" to user %s (%s)' % (order_id,
                                                                                     event.id, 
                                                                                     order.user.id, 
                                                                                     order.user.email))
            
            if not fake:
                htmlbody = env.get_template('mail_order_of_event.html')\
                              .render(event=event, 
                                      tickets=tickets,
                                      order=order, 
                                      as_guest=as_guest, 
                                      account=order.account)
                plainbody = env.get_template('mail_order_of_event.txt')\
                               .render(event=event, 
                                       tickets=tickets,
                                       order=order, 
                                       as_guest=as_guest, 
                                       account=order.account)
                                          
                send_email("Tickee Ticketing <tickets@tick.ee>", 
                           order.user.email, 
                           "Your tickets for '%s' are here!" % event.name, 
                           htmlbody,
                           plainbody)
            
        
        
        order.meta['tickets_sent'] = datetime.datetime.utcnow().strftime("%d-%m-%Y %H:%M:%S UTC%z")
        log_crm("order", order.id, dict(action="mailed",
                                           addressee=order.user.email))
        transaction.commit()
        return True
    except Exception as e:
        tlogger.exception("failed sending mail for order %s: %s" % (order_id, e))
        order.meta['tickets_sent'] = "failed @ %s" % datetime.datetime.utcnow().strftime("%d-%m-%Y %H:%M:%S UTC%z")
        transaction.commit()
        if auto_retry:
            mail_order.retry(exc=e)
        return False

@task(ignore_result=True)
def timeout_sessions(max_allowed_duration=600):
    """
    Times out all order sessions that have been created outside a specific 
    time. 
    
    Args:
        max_allowed_duration: amount of seconds an order has before it 
                              times out.
    
    Returns:
        The amount of orders that were timed out.
    """
    try:
        # calculate the datetime of the oldest allowed session
        begin_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=max_allowed_duration)
        # fetch all order sessions before this datetime
        orders = Session.query(Order).filter(Order.session_start < begin_time)\
                                     .filter(Order.status.in_([STARTED]))
        # time out found orders
        total = 0
        for order in orders:
            log_crm("order", order.id, dict(action="timeout"))
            order.timeout()
            # update ticket type availability
            for tickettype in order.get_ticket_types():
                update_availability.apply_async(args=[tickettype.id], countdown=2)
            total += 1
        return total
    except Exception as e:
        tlogger.exception("failed timing out sessions")