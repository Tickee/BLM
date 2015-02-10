from tickee.accounts.processing import create_account
from tickee.core.currency.processing import create_currency
from tickee.events.eventparts.processing import add_eventpart
from tickee.events.processing import start_event
from tickee.orders.processing import start_order, add_tickets
from tickee.orders.states import TIMEOUT, STARTED, PURCHASED
from tickee.orders.tasks import mail_order, timeout_sessions
from tickee.subscriptions.models import Subscription, FREE
from tickee.tests import BaseTestCase
from tickee.tickets.tasks import create_tickets
from tickee.tickettypes.processing import create_tickettype, link_tickettype_to_event
from tickee.users.processing import create_user


class OrderStartTestCase(BaseTestCase):
    
    def setUp(self):
        super(OrderStartTestCase, self).setUp()
        self.user = create_user("user@example.com")
        create_currency("EUR", "Euro")
        self.account = create_account("accountname", "email")
        self.account.subscription = Subscription(FREE)
        self.event = start_event(self.account.id, "event_name")
        self.eventpart = add_eventpart(self.event.id)
        self.tickettype = create_tickettype(50, 10)
        self.tickettype.is_active = True
        link_tickettype_to_event(self.tickettype, self.event)
        
    # mail_order
    
    def test_mail_tickets(self):
        order = start_order(self.user, self.account)
        add_tickets(order, self.tickettype.id, 5)
        order.checkout()
        order.purchase()
        create_tickets(order)
        self.assertTrue(mail_order(order.id, fake=True))
    
    def test_mail_bad_address(self):
        self.user.email = "badmail"
        order = start_order(self.user, self.account)
        add_tickets(order, self.tickettype.id, 5)
        order.checkout()
        order.purchase()
        create_tickets(order)
        self.assertFalse(mail_order(order.id, fake=True))
        
    def test_mail_empty_order(self):
        order = start_order(self.user, self.account)
        add_tickets(order, self.tickettype.id, 5)
        order.checkout()
        order.purchase()
        self.assertFalse(mail_order(order.id, fake=True))
    
    # timeout_sessions

    def test_timeout_immediately(self):
        order = start_order(self.user, self.account)
        self.assertEqual(order.status, STARTED)
        timeout_sessions(0)
        self.assertEqual(order.status, TIMEOUT)
    
    def test_timeout_after_60(self):
        order = start_order(self.user, self.account)
        self.assertEqual(order.status, STARTED)
        timeout_sessions(60)
        self.assertEqual(order.status, STARTED)
        
    def test_dont_timeout_purchased_orders(self):
        order = start_order(self.user, self.account)
        add_tickets(order, self.tickettype.id, 5)
        order.checkout()
        order.purchase()
        self.assertEqual(order.status, PURCHASED)
        timeout_sessions(0)
        self.assertEqual(order.status, PURCHASED)