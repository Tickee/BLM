import sqlahelper
import tests
import tickee.exceptions as ex
import tickee.logic as logic

Session = sqlahelper.get_session()

class UserCreationTest(tests.BaseTestCase):
    
    # create_user
    
    def test_create_user(self):
        # Setup
        um = logic.UserManager()
        # Test
        um.create_user("")
        
    def test_create_existing_user(self):
        # Setup
        um = logic.UserManager()
        um.create_user("info@example.com")
        # Validate
        self.assertRaises(ex.UserError, um.create_user, "info@example.com")
        
class UserActions(tests.BaseTestCase):
    
    def setUp(self):
        super(UserActions, self).setUp()
        # create user
        um = logic.UserManager()
        self.user = um.create_user("")
        self.user.activate(self.user.activation_key, "")
        
    # reset_user    
    
    def test_reset_user(self):
        # Setup
        um = logic.UserManager()
        # Test
        um.reset_user(self.user.id)
        # Validate
        self.assertFalse(self.user.is_active(),
                        "User is active.")
        
    def test_reset_unexisting_user(self):
        # Setup
        um = logic.UserManager()
        # Test
        self.assertRaises(ex.UserNotFoundError, um.reset_user, 999)
        
    # lookup_user_by_id
    
    def test_lookup_user(self):
        # Setup
        um = logic.UserManager()
        # Test
        user = um.lookup_user_by_id(self.user.id)
        # Validate
        self.assertEqual(user.id, self.user.id, "User id's did not match.")
        
    def test_lookup_unexisting_user(self):
        # Setup
        um = logic.UserManager()
        # Test
        self.assertRaises(ex.UserNotFoundError, um.lookup_user_by_id, 999)