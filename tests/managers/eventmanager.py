import tickee.logic as logic
import sqlahelper
import tests
import tickee.exceptions as ex

Session = sqlahelper.get_session()

class EventCreationTest(tests.BaseTestCase):
    
    def setUp(self):
        super(EventCreationTest, self).setUp()
        # create account
        am = logic.AccountManager()
        self.account = am.create_account("Charlatan", "email")
        
    # start_event
    
    def test_start_event(self):
        # Setup
        em = logic.EventManager()
        # Test
        event = em.start_event(self.account.id, "Event Name")
        # Validate
        self.assertEqual(event.name, "Event Name", "Event has wrong name.")
    
    def test_start_event_unexisting_account(self):
        # Setup
        em = logic.EventManager()
        # Validate
        self.assertRaises(ex.AccountNotFoundError, em.start_event, 999, "Event")
        
    # find_events
    
    def test_find_events_by_id(self):
        # Setup
        am = logic.AccountManager()
        account2 = am.create_account("account_name", "email")
        em = logic.EventManager()
        em.start_event(self.account.id, "Event 1")
        em.start_event(self.account.id, "Event 2")
        em.start_event(account2.id, "Event 3")
        # Test
        events = em.find_events(self.account.id)
        print events
        # Validate
        self.assertEqual(len(events), 2, 
                         "Not all matching events were returned")
        
    # event_exists
    
    def test_check_if_event_exists(self):
        # Setup
        em = logic.EventManager()
        event = em.start_event(self.account.id, "name")
        # Validate
        self.assertTrue(em.event_exists(event.id))
        
    def test_check_if_unexisting_event_exists(self):
        # Setup
        em = logic.EventManager()
        # Validate
        self.assertFalse(em.event_exists(999))
    
    # eventpart_exists
    
    def test_check_if_eventpart_exists(self):
        # Setup
        em = logic.EventManager()
        event = em.start_event(self.account.id, "name")
        eventpart = em.add_eventpart(event.id)
        # Validate
        self.assertTrue(em.eventpart_exists(eventpart.id))
        
    def test_check_if_unexisting_eventpart_exists(self):
        # Setup
        em = logic.EventManager()
        # Validate
        self.assertFalse(em.eventpart_exists(999))
    
    # lookup_event_by_id
    
    def test_lookup_event_by_id(self):
        # Setup
        em = logic.EventManager()
        event = em.start_event(self.account.id, "name")
        # Test
        event_found = em.lookup_event_by_id(event.id)
        # Validate
        self.assertEqual(event, event_found, "Event did not match")
    
    def test_lookup_unexisting_event_by_id(self):
        # Setup
        em = logic.EventManager()
        # Validate
        self.assertRaises(ex.EventNotFoundError, em.lookup_event_by_id, 999)
    
    # lookup_eventpart_by_id

    def test_lookup_eventpart_by_id(self):
        # Setup
        em = logic.EventManager()
        event = em.start_event(self.account.id, "name")
        eventpart = em.add_eventpart(event.id)
        # Test
        eventpart_found = em.lookup_eventpart_by_id(eventpart.id)
        # Validate
        self.assertEqual(eventpart, eventpart_found, "Eventpart did not match")
    
    def test_lookup_unexisting_eventpart_by_id(self):
        # Setup
        em = logic.EventManager()
        # Validate
        self.assertRaises(ex.EventPartNotFoundError, em.lookup_eventpart_by_id, 999)


class EventManagementTest(tests.BaseTestCase):
    
    def setUp(self):
        super(EventManagementTest, self).setUp()
        # create account
        am = logic.AccountManager()
        self.account = am.create_account("Charlatan", "email")
        # create event
        em = logic.EventManager()
        self.event = em.start_event(self.account.id, "Charlatan")
        # create eventpart
        self.eventpart = em.add_eventpart(self.event.id, "Day 1")
    
    # add_eventpart
    
    def test_add_eventpart(self):
        # Setup
        em = logic.EventManager()
        # Test
        eventpart = em.add_eventpart(self.event.id)
        # Validate
        self.assertEqual(eventpart.event_id, self.event.id, 
                         "The eventpart is not connected to the event")
    
    def test_add_eventpart_to_unexisting_event(self):
        # Setup
        em = logic.EventManager()
        # Validate
        self.assertRaises(ex.EventNotFoundError, em.add_eventpart, 999)
        
    def test_add_eventpart_with_unexisting_venue(self):
        # Setup
        em = logic.EventManager()
        # Validate
        self.assertRaises(ex.VenueNotFoundError, em.add_eventpart, 
                          self.event.id, venue_id=999)
    
    # add_venue_to_event
    
    def test_add_venue_to_event(self):
        # Setup
        em = logic.EventManager()
        vm = logic.VenueManager()
        venue = vm.create_venue("Marktplein Lokeren")
        # Test
        em.add_venue_to_event(self.event.id, venue.id)
        # Validate
        self.assertEqual(self.event.venue, venue,
                         "Venue was not connected successfully")
        
    def test_add_venue_to_unexisting_event(self):
        # Setup
        em = logic.EventManager()
        vm = logic.VenueManager()
        venue = vm.create_venue("Marktplein Lokeren")
        # Validate
        self.assertRaises(ex.EventNotFoundError, em.add_venue_to_event,
                          999, venue.id)
        
    def test_add_unexisting_venue_to_event(self):
        # Setup
        em = logic.EventManager()
        # Validate
        self.assertRaises(ex.VenueNotFoundError, em.add_venue_to_event,
                          self.event.id, 999)
    
    # add_venue_to_eventpart    
    
    def test_add_venue_to_eventpart(self):
        # Setup
        em = logic.EventManager()
        vm = logic.VenueManager()
        venue = vm.create_venue("Marktplein Lokeren")
        # Test
        em.add_venue_to_eventpart(self.eventpart.id, venue.id)
        # Validate
        self.assertEqual(self.eventpart.venue, venue,
                         "Venue was not connected successfully")
        
    def test_add_venue_to_unexisting_eventpart(self):
        # Setup
        em = logic.EventManager()
        vm = logic.VenueManager()
        venue = vm.create_venue("Marktplein Lokeren")
        # Validate
        self.assertRaises(ex.EventPartNotFoundError, em.add_venue_to_eventpart,
                          999, venue.id)
        
    def test_add_unexisting_venue_to_eventpart(self):
        # Setup
        em = logic.EventManager()
        vm = logic.VenueManager()
        # Validate
        self.assertRaises(ex.VenueNotFoundError, em.add_venue_to_eventpart,
                          self.eventpart.id, 999)
    