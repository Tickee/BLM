from tickee.accounts.processing import create_account
from tickee.events.processing import start_event
from tickee.tests import BaseTestCase
import sqlahelper
from tickee.events.eventparts.processing import add_eventpart
from tickee.tickettypes.processing import create_tickettype, link_tickettype_to_event
from tickee.core.currency.processing import create_currency
Session = sqlahelper.get_session()

class TicketTypeModelTestCase(BaseTestCase):
    
    def setUp(self):
        super(TicketTypeModelTestCase, self).setUp()
        create_currency("EUR", "Euro")
        self.account = create_account("accountname", "email")
        self.event = start_event(self.account.id, "event name")
        add_eventpart(self.event.id)
        
    # -- creation
    
    def test_create_tickettype(self):
        tt = create_tickettype(100, 10)
        link_tickettype_to_event(tt, self.event)
        self.assertEqual(tt.units, 10)
        self.assertEqual(tt.price, 100)
        self.assertEqual(tt.get_handling_fee(), 0)
    
    # -- setting handling fee
    
    def test_no_handling_fee_on_free_types(self):
        tt = create_tickettype(0, 10)
        link_tickettype_to_event(tt, self.event)
        self.event.set_handling_fee(50)
        self.assertEqual(tt.get_handling_fee(), 0)
    
    def test_set_handling_fee_via_event(self):
        tt = create_tickettype(100, 10)
        link_tickettype_to_event(tt, self.event)
        self.event.set_handling_fee(50)
        self.assertEqual(tt.price, 100)
        self.assertEqual(tt.get_handling_fee(), 50)
        
    def test_set_handling_fee_via_account(self):
        tt = create_tickettype(100, 10)
        link_tickettype_to_event(tt, self.event)
        self.account.set_handling_fee(50)
        self.assertEqual(tt.price, 100)
        self.assertEqual(tt.get_handling_fee(), 50)
        
    def test_handling_fee_precedences_1(self):
        # setting handling fee on event > default of account
        tt = create_tickettype(100, 10)
        link_tickettype_to_event(tt, self.event)
        self.account.set_handling_fee(50)
        self.event.set_handling_fee(40)
        self.assertEqual(tt.get_handling_fee(), 40)
        
    def test_handling_fee_precedences_2(self):
        # setting handling fee on tt > event > default of account
        tt = create_tickettype(100, 10)
        link_tickettype_to_event(tt, self.event)
        self.event.set_handling_fee(40)
        tt.set_handling_fee(30)
        self.account.set_handling_fee(50)
        self.assertEqual(tt.get_handling_fee(), 30)
        
    