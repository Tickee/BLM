from tickee.accounts.processing import create_account
from tickee.core.currency.processing import create_currency
from tickee.db.models.order import Order
from tickee.db.models.ticketorder import TicketOrder
from tickee.events.eventparts.processing import add_eventpart
from tickee.events.processing import start_event
from tickee.orders.processing import start_order, add_tickets
from tickee.subscriptions.models import Subscription, FREE
from tickee.tests import BaseTestCase
from tickee.tickets.manager import tickets_from_order
from tickee.tickets.tasks import create_tickets, mail_ticket
from tickee.tickettypes.processing import create_tickettype, link_tickettype_to_event
from tickee.users.processing import create_user
import sqlahelper


Session = sqlahelper.get_session()

class TaskTestCase(BaseTestCase):
    
    def setUp(self):
        super(TaskTestCase, self).setUp()
        self.order = Order(None, None)
        Session.add(self.order)
        Session.flush()
        ticketorder = TicketOrder(self.order.id, None, 5)
        Session.add(ticketorder)
        Session.flush()

    # create_tickets
    
    def test_uncreated_tickets_from_order(self):
        self.assertEqual(len(tickets_from_order(self.order)),
                         0)
    
    def test_created_tickets_from_order(self):
        create_tickets(self.order)
        self.assertEqual(len(tickets_from_order(self.order)),
                         5)
    
    def test_created_double_tickets_from_order(self):
        create_tickets(self.order)
        self.assertEqual(len(tickets_from_order(self.order)),
                         5)
    
    # has_created_ticket
    
    
    
class TicketMailingTestCase(BaseTestCase):
    
    def setUp(self):
        super(TicketMailingTestCase, self).setUp()
        self.user = create_user("valid@example.com")
        self.invalid_mail_user = create_user("invalidexample.com")
        self.account = create_account("accountname", "email")
        self.account.subscription = Subscription(FREE)
        create_currency("EUR", "Euro")
        self.event = start_event(self.account.id, "event_name")
        self.eventpart = add_eventpart(self.event.id)
        self.tickettype = create_tickettype(50, 10)
        self.tickettype.is_active = True
        link_tickettype_to_event(self.tickettype, self.event)
    
    # mail_ticket

    def test_mail_ticket(self):
        order = start_order(self.user, self.account)
        add_tickets(order, self.tickettype.id, 5)
        create_tickets(order)
        self.assertTrue(mail_ticket(1, fake=True))
        
    def test_send_to_invalid_mail(self):
        order = start_order(self.invalid_mail_user, self.account)
        add_tickets(order, self.tickettype.id, 5)
        create_tickets(order)
        self.assertFalse(mail_ticket(1, fake=True))
        
    