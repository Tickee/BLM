from tickee.accounts.processing import create_account
from tickee.core.currency.processing import create_currency
from tickee.events.eventparts.processing import add_eventpart
from tickee.events.processing import start_event
from tickee.orders.processing import start_order, add_tickets, finish_order
from tickee.orders.states import STARTED
from tickee.paymentproviders.processing import get_or_create_transaction_statistic
from tickee.subscriptions.models import Subscription, FREE
from tickee.tests import BaseTestCase
from tickee.tickettypes.processing import create_tickettype, link_tickettype_to_event
from tickee.tickettypes.states import AVAILABLE, CLAIMED, SOLD
from tickee.users.processing import create_user
import tickee.exceptions as ex

class OrderStartTestCase(BaseTestCase):
    
    def setUp(self):
        super(OrderStartTestCase, self).setUp()
        self.user = create_user("email@example.com")
        self.user2 = create_user("email2@example.com")
        self.invalid_mail_user = create_user("email")
        self.account = create_account("accountname", "email")
        self.account2 = create_account("accountname2", "email")
        self.account.subscription = Subscription(FREE)
        
    # start_order
    
    def test_start_order(self):
        order = start_order(self.user, self.account)
        self.assertEqual(order.account, self.account)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, STARTED)
        
    def test_start_two_seperate_orders(self):
        order1 = start_order(self.user, self.account)
        order2 = start_order(self.user2, self.account2)
        self.assertNotEqual(order1, order2)
        self.assertNotEqual(order1.order_key, order2.order_key)
    
    def test_start_two_seperate_orders_for_account(self):
        order1 = start_order(self.user, self.account)
        order2 = start_order(self.user2, self.account)
        self.assertNotEqual(order1, order2)
        self.assertNotEqual(order1.order_key, order2.order_key)
    
    def test_start_two_seperate_orders_by_user(self):
        order1 = start_order(self.user, self.account)
        order2 = start_order(self.user, self.account2)
        self.assertNotEqual(order1, order2)
        self.assertNotEqual(order1.order_key, order2.order_key)
    
    def test_start_two_same_orders(self):
        order1 = start_order(self.user, self.account)
        order2 = start_order(self.user, self.account)
        self.assertEqual(order1, order2)
        self.assertEqual(order1.order_key, order2.order_key)

    def test_start_order_late_user_binding(self):
        order = start_order(None, self.account)
        order2 = start_order(None, self.account)
        self.assertNotEqual(order, order2)
    
        
class TicketAddingTestCase(OrderStartTestCase):
    
    def setUp(self):
        super(TicketAddingTestCase, self).setUp()
        create_currency("EUR", "Euro")
        self.event = start_event(self.account.id, "event_name")
        self.eventpart = add_eventpart(self.event.id)
        
        self.event2 = start_event(self.account2.id, "event_name2")
        self.eventpart2 = add_eventpart(self.event2.id)
        
        self.another_tickettype = create_tickettype(50, 10)
        self.another_tickettype.is_active = True
        link_tickettype_to_event(self.another_tickettype, self.event2)
        
        self.tickettype = create_tickettype(50, 10)
        self.tickettype.is_active = True
        link_tickettype_to_event(self.tickettype, self.event)
        
        self.free_tickettype = create_tickettype(0, 10)
        self.free_tickettype.is_active = True
        link_tickettype_to_event(self.free_tickettype, self.event)
        
        self.tickettype2 = create_tickettype(50, 10)
        self.tickettype2.is_active = True
        link_tickettype_to_event(self.tickettype2, self.event)
        
        self.unlinked_tickettype = create_tickettype(50, 10)
        self.unlinked_tickettype.is_active = True
        
        self.inactive_tickettype = create_tickettype(50, 10)
        self.inactive_tickettype.is_active = False
        link_tickettype_to_event(self.inactive_tickettype, self.event)

    # add_tickets
    
    def test_no_tickets(self):
        order = start_order(self.user, self.account)
        self.assertEqual(len(order.get_ticketorders()), 0)
        
    def test_add_tickets(self):
        order = start_order(self.user, self.account)
        add_tickets(order, self.tickettype.id, 5)
        self.assertEqual(len(order.get_ticketorders()), 1)
        self.assertEqual(order.get_ticketorders()[0].amount, 5)
        self.assertEqual(order.get_ticketorders()[0].ticket_type_id, self.tickettype.id)
        
    def test_update_tickets(self):
        order = start_order(self.user, self.account)
        add_tickets(order, self.tickettype.id, 5)
        add_tickets(order, self.tickettype.id, 4)
        self.assertEqual(len(order.get_ticketorders()), 1)
        self.assertEqual(order.get_ticketorders()[0].amount, 4)
        self.assertEqual(order.get_ticketorders()[0].ticket_type_id, self.tickettype.id)
    
    def test_add_different_tickets(self):
        order = start_order(self.user, self.account)
        add_tickets(order, self.tickettype.id, 5)
        add_tickets(order, self.tickettype2.id, 4)
        self.assertEqual(len(order.get_ticketorders()), 2)
        
    def test_add_unlinked_ticket(self):
        order = start_order(self.user, self.account)
        self.assertRaises(ex.EventNotFoundError, add_tickets, order, self.unlinked_tickettype.id, 5)
    
    def test_add_invalid_amount_tickets(self):
        order = start_order(self.user, self.account)
        self.assertRaises(ex.InvalidAmountError, add_tickets, order, self.tickettype.id, -1)
        
    def test_add_tickets_to_locked_order(self):
        order = start_order(self.user, self.account)
        add_tickets(order, self.tickettype.id, 5)
        order.lock()
        self.assertRaises(ex.OrderLockedError, add_tickets, order, self.tickettype.id, 5)
        
    def test_adding_inactive_tickettype(self):
        order = start_order(self.user, self.account)
        self.assertRaises(ex.InactiveTicketTypeError, add_tickets, order, self.inactive_tickettype.id, 5)
    
    def test_adding_someone_elses_tickettype(self):
        order = start_order(self.user, self.account)
        self.assertRaises(ex.AccountError, add_tickets, order, self.another_tickettype.id, 5)
    
    def test_updating_too_many(self):
        order = start_order(self.user, self.account)
        add_tickets(order, self.tickettype.id, 5)
        add_tickets(order, self.tickettype.id, 9)
        add_tickets(order, self.tickettype.id, 10)
        self.assertRaises(ex.AmountNotAvailableError, add_tickets, order, self.tickettype.id, 11)
    
    def test_claiming_all_tickets(self):
        order = start_order(self.user, self.account)
        add_tickets(order, self.tickettype.id, 10)
        self.assertEqual(self.tickettype.availability, CLAIMED)
    
    def test_adding_too_many(self):
        order = start_order(self.user, self.account)
        self.assertRaises(ex.AmountNotAvailableError, add_tickets, order, self.tickettype.id, 11)
    
    def test_adding_zero(self):
        order = start_order(self.user, self.account)
        self.assertRaises(ex.AmountNotAvailableError, add_tickets, order, self.tickettype.id, 0)
        
    def test_remove_on_update_to_zero(self):
        order = start_order(self.user, self.account)
        add_tickets(order, self.tickettype.id, 5)
        self.assertEqual(len(order.ordered_tickets.all()), 1)
        add_tickets(order, self.tickettype.id, 0)
        self.assertEqual(len(order.ordered_tickets.all()), 0)
    
    def test_add_tickets_when_no_transactions_available(self):
        order = start_order(self.user, self.account)
        get_or_create_transaction_statistic(self.account).amount = 500
        self.assertRaises(ex.SubscriptionError, add_tickets, order, self.tickettype.id, 5)
    
    def test_add_free_tickets_when_no_transaction_available(self):
        order = start_order(self.user, self.account)
        get_or_create_transaction_statistic(self.account).amount = 500
        add_tickets(order, self.free_tickettype.id, 5)
    
    def test_add_free_tickets(self):
        order = start_order(self.user, self.account)
        add_tickets(order, self.free_tickettype.id, 5)
    
    def test_add_tickets_to_order_with_no_user(self):
        order = start_order(None, self.account)
        add_tickets(order, self.tickettype.id, 5)
        self.assertEqual(len(order.get_ticketorders()), 1)
        self.assertEqual(order.get_ticketorders()[0].amount, 5)
        self.assertEqual(order.get_ticketorders()[0].ticket_type_id, self.tickettype.id)
    
    # finish_order
    
    def test_finish_unlocked_order(self):
        order = start_order(self.user, self.account)
        self.assertRaises(ex.OrderError, finish_order, order, send_mail=False)
    
    def test_finish_order(self):
        order = start_order(self.user, self.account)
        add_tickets(order, self.tickettype.id, 9)
        order.checkout()
        finish_order(order, send_mail=False)
        self.assertEqual(self.tickettype.availability, AVAILABLE)
        self.assertEqual(len(order.get_tickets()), 9)
    
    def test_finish_full_order(self):
        order = start_order(self.user, self.account)
        add_tickets(order, self.tickettype.id, 10)
        order.checkout()
        finish_order(order, send_mail=False)
        self.assertEqual(self.tickettype.availability, SOLD)
    
    def test_finish_binding_full_order(self):
        order = start_order(None, self.account)
        add_tickets(order, self.tickettype.id, 10)
        order.checkout(self.user)
    
    def test_finish_unbound_full_order(self):
        order = start_order(None, self.account)
        add_tickets(order, self.tickettype.id, 10)
        self.assertRaises(ex.OrderError, order.checkout)
