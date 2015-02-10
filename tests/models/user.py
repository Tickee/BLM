from tickee import logic
from tickee.db.models.event import Event
from tickee.db.models.user import User
import sqlahelper
import tests
import tickee.exceptions as ex

Session = sqlahelper.get_session()

um = logic.UserManager()

class CreateUserTest(tests.BaseTestCase):
    
    def setUp(self):
        super(CreateUserTest, self).setUp()
    
    def test_create_user(self):
        # Test
        user = User("info@example.com")
        # Validate
        self.assertFalse(user.has_usable_password())
        self.assertEquals("info@example.com", user.email)
        self.assertFalse(user.is_active())
        
    def test_activate_user(self):
        # Prepare
        user = User("info@example.com")
        activation_key = user.activation_key
        # Test
        user.activate(activation_key, "test")
        # Validate
        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.is_active())
        self.assertTrue(user.check_password("test"))
        self.assertFalse(user.check_password("test2"))
        
    def test_reset_user(self):
        # Prepare
        user = User("info@example.com")
        activation_key = user.activation_key
        user.activate(activation_key, "test")
        # Test
        user.reset()
        # Validate
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.is_active())
        self.assertFalse(user.check_password("test"))
        