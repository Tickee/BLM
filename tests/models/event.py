from tickee import logic
from tickee.db.models.event import Event
import sqlahelper
import tests
import tickee.exceptions as ex

Session = sqlahelper.get_session()

am = logic.AccountManager()
vm = logic.VenueManager()
tm = logic.TicketManager()
em = logic.EventManager()
om = logic.OrderManager()

class CreateEventTest(tests.BaseTestCase):
    
    def setUp(self):
        super(CreateEventTest, self).setUp()
        self.account = am.create_account("accountname", "email")
        self.venue = vm.create_venue("venuename")
    
    # init
    
    def test_create_event(self):
        # Test
        event = Event("name", self.venue.id, self.account.id)
        Session.add(event)
        Session.flush()
        # Validate
        self.assertIsInstance(event, Event)
        self.assertEqual(event.name, "name")
        self.assertEqual(event.venue, self.venue)
        self.assertEqual(event.account, self.account)

class ModifyEventTest(tests.BaseTestCase):
    
    def setUp(self):
        super(ModifyEventTest, self).setUp()
        self.account = am.create_account("accountname", "email")
        self.venue = vm.create_venue("venuename")
        self.event = em.start_event(self.account.id, "eventname")
        self.eventpart = em.add_eventpart(self.event.id, "eventpartname")
        self.tickettype = tm.create_ticket_type(self.eventpart.id, 1, 10, "tickettypename", "EUR")
    
    # publish

    def test_publish_event(self):
        # Validate
        self.assertFalse(self.tickettype.is_active)
        self.assertFalse(self.event.is_active)
        # Test
        self.event.publish()
        # Validate
        self.assertTrue(self.tickettype.is_active)
        self.assertTrue(self.event.is_active)
    
    # get_ticket_types
    
    def test_empty_listing_tickettypes(self):
        event = em.start_event(self.account.id, "eventname")
        self.assertListEqual(event.get_ticket_types(), [])
    
    def test_listing_tickettypes(self):
        # Validate
        self.assertListEqual(self.event.get_ticket_types(), [self.tickettype])
    
    # get_availabilty

    def test_available_availability(self):
        pass # Todo: Unit tests for get_availability

    # get_tickets
    
    def test_tickets(self):
        pass # Todo: Unit tests for get_tickets