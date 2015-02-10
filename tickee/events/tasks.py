from celery.task import task
from jinja2.environment import Environment
from jinja2.loaders import PackageLoader
from sqlalchemy.sql.expression import distinct
from tickee.core import entrypoint
from tickee.core.crm.tasks import log_crm
from tickee.db.models.account import Account
from tickee.db.models.event import Event
from tickee.db.models.eventpart import EventPart
from tickee.db.models.order import Order
from tickee.db.models.ticketorder import TicketOrder
from tickee.db.models.tickettype import TicketTypeEventPartAssociation, \
    TicketType
from tickee.db.models.user import User
from tickee.events.manager import lookup_event_by_id
from tickee.orders.states import PURCHASED
from tickee.users.manager import lookup_user_by_id
from tickee.users.tasks import mail_user
import datetime
import logging
import random
import sqlahelper
import transaction

Session = sqlahelper.get_session()

env = Environment(loader=PackageLoader('tickee', 'templates'))
blogger = logging.getLogger('blm.events')


@task(name="routine.event_in_48_hours_reminder",
      ignore_result=True)
def event_in_48_hours_reminder():
    """Looks up all happening in 48 hours and sends notification mails"""
    # find all events happening between now and 48 hours
    now = datetime.datetime.utcnow()
    in_48_hours = now + datetime.timedelta(hours=48) 
    events = Session.query(Event).join(EventPart).filter(EventPart.starts_on >= now)\
                                                 .filter(EventPart.starts_on < in_48_hours).all()
    for event in set(events):
        # only send if not sent before
        if not event.meta.get('notifications_sent', False):
            event_notification.delay(event.id)
            event.meta['notifications_sent'] = True
    transaction.commit()



@task(name="event.send_notification_mails", 
      ignore_result=True)
def event_notification(event_id):
    """Sends a notification mail informing all attendees to bring their tickets
    with them."""
    blogger.info('sending notifications for event %s' % event_id)
    users = Session.query(distinct(User.id))\
                   .join(Order, TicketOrder, TicketType, TicketTypeEventPartAssociation, EventPart, Event)\
                   .filter(Event.id==event_id)\
                   .filter(Order.status==PURCHASED)\
                   .all()
    count = 0
    for user_id, in users:
        batchnr = count / 20 # twenty mails per batch = 2 minute bursts
        single_notification_mail.apply_async(args=[event_id, user_id], countdown=batchnr*5*60)
        count += 1


@task(name="user.send_notification_mail",
      rate_limit="10/m", 
      ignore_result=True)
def single_notification_mail(event_id, user_id):
    """Sends a notification mail informing an attendee to 
    bring his or her tickets"""
    user = lookup_user_by_id(user_id)
    event = lookup_event_by_id(event_id)
    
    # do not send if user already received one
    if 'received_event_notification' in user.meta:
        blogger.info('skipping event notification since user already has received one.')
        return
    
    subject = "Reminder: %s (%s)" % (event.name, event.account.name)
    html_content = env.get_template('event_in_48_hours.html').render(user=user, event=event)
    plain_content = env.get_template('event_in_48_hours.txt').render(user=user, event=event)
    
    blogger.info('sending event notification mail to user %s' % user_id)
    success = mail_user(user_id, subject, html_content, plain_content)
#    success = random.choice([True, True, True, True, True, False])
    if not success:
        single_notification_mail.retry(countdown=120+random.randint(1,60))
    else:
        user.meta['received_event_notification'] = False
        transaction.commit()