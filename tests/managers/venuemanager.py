import sqlahelper
import tests
import tickee.exceptions as ex
import tickee.logic as logic

Session = sqlahelper.get_session()

class VenueCreationTest(tests.BaseTestCase):
    
    # create_venue
    
    def test_create_venue(self):
        # Setup
        vm = logic.VenueManager()
        # Test
        venue = vm.create_venue("Charlatan")
        # Validate
        self.assertEqual(venue.name, "Charlatan", "Name does not match.")
        
    def test_create_duplicate_venue(self):
        # Setup
        vm = logic.VenueManager()
        vm.create_venue("Charlatan")
        # Validate
        self.assertRaises(ex.VenueExistsError, vm.create_venue, "Charlatan")
    
    # create_address
    
    def test_create_address(self):
        # Setup
        vm = logic.VenueManager()
        # Test
        address = vm.create_address("street_line1", 'street_line2', 
                                    'postal_code', 'city', 'country_code')
        # Validate
        self.assertEqual(address.street_line1, "street_line1", 
                         "street_line1 did not match")
        self.assertEqual(address.street_line2, "street_line2", 
                         "street_line2 did not match")
        self.assertEqual(address.postal_code, "postal_code", 
                         "postal_code did not match")
        self.assertEqual(address.city, "city", 
                         "city did not match")
        self.assertEqual(address.country, "country_code", 
                         "country_code did not match")
    
    # lookup_venue_by_id
    
    def test_lookup_venue(self):
        # Setup
        vm = logic.VenueManager()
        venue = vm.create_venue("Charlatan")
        # Validate
        self.assertEqual(vm.lookup_venue_by_id(venue.id), venue)
        
    def test_lookup_unexisting_venue(self):
        # Setup
        vm = logic.VenueManager()
        # Validate
        self.assertRaises(ex.VenueNotFoundError, vm.lookup_venue_by_id, 999)
        
    # lookup_address_by_id    
    
    def test_lookup_address(self):
        # Setup
        vm = logic.VenueManager()
        address = vm.create_address("street_line1", 'street_line2', 
                                    'postal_code', 'city', 'country_code')
        # Validate
        self.assertEqual(vm.lookup_address_by_id(address.id), address)
        
    def test_lookup_unexisting_address(self):
        # Setup
        vm = logic.VenueManager()
        # Validate
        self.assertRaises(ex.AddressNotFoundError, vm.lookup_address_by_id, 999)
    
    # find_venue_by_filter
    
    # -- name filter
    
    def test_find_multiple_venues_by_name_filter(self):
        # Setup
        vm = logic.VenueManager()
        vm.create_venue("Charlatan")
        vm.create_venue("Varnage")
        # Test
        matches = vm.find_venues_by_filter("ar")
        # Validate
        self.assertEqual(len(matches), 2, 
                         "Incorrect number of results (%s) found." % len(matches))
        
    def test_find_one_venue_by_name_filter(self):
        # Setup
        vm = logic.VenueManager()
        vm.create_venue("Charlatan")
        vm.create_venue("Varnage")
        # Test
        matches = vm.find_venues_by_filter("arla")
        # Validate
        self.assertEqual(len(matches), 1, 
                         "Incorrect number of results (%s) found." % len(matches))
    
    # -- limit 
    
    def test_limited_find_venue(self):
        # Setup
        vm = logic.VenueManager()
        vm.create_venue("Charlatan")
        vm.create_venue("Varnage")
        # Test
        matches = vm.find_venues_by_filter("ar", limit=1)
        # Validate
        self.assertEqual(len(matches), 1, 
                         "Incorrect number of results (%s) found." % len(matches))
        
        