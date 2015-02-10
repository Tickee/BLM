from tickee.db.models.user import User
import sqlahelper
import tests
import tickee.exceptions as ex
import tickee.logic as logic

Session = sqlahelper.get_session()

class TicketTypeCreationTest(tests.BaseTestCase):
    
    def setUp(self):
        super(TicketTypeCreationTest, self).setUp()
        # Create a user
        self.user = User("email")
        Session.add(self.user)
        Session.flush()
        # Create Account
        am = logic.AccountManager()
        self.account = am.create_account("Charlatan", "email")
        # Create Event
        em = logic.EventManager()
        self.event = em.start_event(self.account.id, "Gentse Feesten @ Charlatan")
        # Create EventPart
        self.eventpart = em.add_eventpart(self.event.id)
    
    # create_ticket_type

    def test_add_ticket_type(self):
        # Setup
        tm = logic.TicketManager()
        # Test
        tm.create_ticket_type(self.eventpart.id, 5, 10)
        
    def test_add_negative_priced_ticket_type(self):
        # Setup
        tm = logic.TicketManager()
        # Validate
        self.assertRaises(ex.InvalidPriceError, tm.create_ticket_type, 
                          self.eventpart.id, -1, 10)
    
    def test_add_zero_amount_ticket_type(self):
        # Setup
        tm = logic.TicketManager()
        # Validate
        tm.create_ticket_type(self.eventpart.id, 5, 0)
    
    def test_add_negative_amount_ticket_type(self):
        # Setup
        tm = logic.TicketManager()
        # Validate
        self.assertRaises(ex.InvalidAmountError, tm.create_ticket_type, 
                          self.eventpart.id, 5, -1)
        
    def test_add_to_unexisting_eventpart(self):
        # Setup
        tm = logic.TicketManager()
        # Validate
        self.assertRaises(ex.EventPartNotFoundError, tm.create_ticket_type, 
                          999, 5, -1)