from tickee.accounts.processing import create_account
from tickee.core.currency.processing import create_currency
from tickee.events.eventparts.processing import add_eventpart
from tickee.events.processing import start_event
from tickee.orders.manager import get_started_order, get_orders_of_user, lookup_order_by_id, lookup_order_by_key, \
    lookup_order_by_payment_key
from tickee.orders.processing import start_order
from tickee.tests import BaseTestCase
from tickee.tickettypes.processing import create_tickettype, link_tickettype_to_event
from tickee.users.processing import create_user
import tickee.exceptions as ex

class OrderStartTestCase(BaseTestCase):
    
    def setUp(self):
        super(OrderStartTestCase, self).setUp()
        self.user = create_user("user@example.com")
        self.user2 = create_user("user@example2.com")
        create_currency("EUR", "Euro")
        self.account = create_account("accountname", "email")
        self.account2 = create_account("accountname2", "email")
        self.event = start_event(self.account.id, "event_name")
        self.eventpart = add_eventpart(self.event.id)
        self.tickettype = create_tickettype(50, 10)
        self.tickettype.is_active = True
        link_tickettype_to_event(self.tickettype, self.event)
        
    # get_started_order
    
    def test_started_orders(self):
        order = start_order(self.user, self.account)
        order2 = start_order(self.user2, self.account)
        order3 = start_order(self.user, self.account2)
        order4 = start_order(self.user2, self.account2)
        started_order = get_started_order(self.user.id, self.account.id)
        self.assertEqual(order, started_order)
        self.assertNotEqual(order, order2)
        self.assertNotEqual(order2, order3)
        self.assertNotEqual(order3, order4)
        
    def test_no_started_orders(self):
        self.assertRaises(ex.OrderNotFoundError, get_started_order, self.user.id, self.account.id)
    
    # get_orders_of_user
    
    def test_get_orders_of_user(self):
        order = start_order(self.user, self.account)
        order2 = start_order(self.user, self.account2)
        order3 = start_order(self.user2, self.account)
        orders = get_orders_of_user(self.user.id)
        self.assertEqual(len(orders), 2)
        self.assertIn(order, orders)
        self.assertIn(order2, orders)
        self.assertNotIn(order3, orders)
    
    # lookup_order_by_id
    
    def test_get_order_by_id(self):
        order = start_order(self.user, self.account)
        order2 = start_order(self.user2, self.account)
        found_order = lookup_order_by_id(order.id)
        self.assertEqual(order, found_order)
        self.assertNotEqual(found_order, order2)
        
    def test_get_unexisting_order_by_id(self):
        self.assertRaises(ex.OrderNotFoundError, lookup_order_by_id, 0)
        
    # lookup_order_by_key
    
    def test_get_order_by_key(self):
        order = start_order(self.user, self.account)
        order2 = start_order(self.user2, self.account)
        found_order = lookup_order_by_key(order.order_key)
        self.assertEqual(order, found_order)
        self.assertNotEqual(found_order, order2)
        
    def test_get_unexisting_order_by_key(self):
        self.assertRaises(ex.OrderNotFoundError, lookup_order_by_key, "0000")
    
    # lookup_order_by_payment_key
    
    def test_get_order_by_payment_key(self):
        order = start_order(self.user, self.account)
        order2 = start_order(self.user2, self.account)
        found_order = lookup_order_by_payment_key(order.payment_key)
        self.assertEqual(order, found_order)
        self.assertNotEqual(found_order, order2)
        
    def test_get_unexisting_order_by_payment_key(self):
        self.assertRaises(ex.OrderNotFoundError, lookup_order_by_payment_key, "0000")
    
    # get_order_query
