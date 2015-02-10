from tickee.db.models.account import Account
from tickee.db.models.user import User, UserAccountAssociation
import sqlahelper
import tests
import tickee.exceptions as ex
import tickee.logic as logic

Session = sqlahelper.get_session()

class AccountTest(tests.BaseTestCase):
    
    # create_account
    
    def test_create_account(self):
        # Setup
        am = logic.AccountManager()
        # Test
        account = am.create_account("Charlatan", "email")
        # Validate
        self.assertEqual(account.name, "Charlatan", 
                         "Name was not saved")
        self.assertEqual(account.email, "email",
                         "Email was not saved")
        
    def test_create_duplicate_account(self):
        # Setup
        am = logic.AccountManager()
        # Test
        am.create_account("Charlatan", "email")
        # Validate
        self.assertRaises(ex.AccountError, am.create_account, "Charlatan", "")
    
    # acount_exists
    
    def test_account_exists(self):
        # Setup
        am = logic.AccountManager()
        am.create_account("Charlatan", "email")
        # Validate
        self.assertTrue(am.account_exists("Charlatan"))
        
    def test_account_does_not_exist(self):
        # Setup
        am = logic.AccountManager()
        # Validate
        self.assertFalse(am.account_exists("Charlatan"))
        
    # lookup_account_by_id
        
    def test_lookup_existing_account(self):
        # Setup
        am = logic.AccountManager()
        account = am.create_account("Charlatan", "email")
        # Validate
        self.assertIsInstance(am.lookup_account_by_id(account.id), Account, 
                              "Did not find the account.")
    
    def test_lookup_unexisting_account(self):
        # Setup
        am = logic.AccountManager()
        # Validate
        self.assertRaises(ex.AccountNotFoundError, am.lookup_account_by_id, 999)
        
        
class AccountUserTest(tests.BaseTestCase):
    
    def setUp(self):
        super(AccountUserTest, self).setUp()
        # Create account
        am = logic.AccountManager()
        self.account = am.create_account("Charlatan", "email")
        # Create a user
        self.user = User("email")
        Session.add(self.user)
        Session.flush()
    
    # add_user
    
    def test_connect_user_to_account(self):
        # Setup
        am = logic.AccountManager()
        # Test
        am.add_user(self.account.id, self.user.id)

    def test_connect_already_connected_user(self):
        # Setup
        am = logic.AccountManager()
        am.add_user(self.account.id, self.user.id)
        # Validate
        self.assertRaises(ex.UserAssociationError, am.add_user, 
                          self.account.id, self.user.id)
        
    def test_connecting_to_unexisting_account(self):
        # Setup
        am = logic.AccountManager()
        # Validate
        self.assertRaises(ex.AccountNotFoundError, am.add_user, 
                          999, self.user.id)
        
    def test_connecting_unexisting_user(self):
        # Setup
        am = logic.AccountManager()
        # Validate
        self.assertRaises(ex.UserNotFoundError, am.add_user, 
                          self.account.id, 999)
        
    # account_associates
    
    def test_unexisting_account_associates(self):
        # Setup
        am = logic.AccountManager()
        # Validate
        self.assertRaises(ex.AccountNotFoundError, am.account_associates, 999)
        
    def test_empty_associates(self):    
        # Setup
        am = logic.AccountManager()
        # Test
        assocs = am.account_associates(self.account.id)
        # Validate
        self.assertEqual(len(assocs), 0, 
                         "Did not find the correct amount of associates")
    
    def test_existing_account_associates(self):
        # Setup
        am = logic.AccountManager()
        am.add_user(self.account.id, self.user.id)
        # Test
        assocs = am.account_associates(self.account.id)
        # Validate
        self.assertEqual(len(assocs), 1, 
                         "Did not find the correct amount of associates")
        
    def test_associate_user_with_two_accounts(self):
        # Setup
        am = logic.AccountManager()
        account2 = am.create_account("Test", "email")
        am.add_user(self.account.id, self.user.id)
        am.add_user(account2.id, self.user.id)
        # Test
        assocs_acc1 = am.account_associates(self.account.id)
        assocs_acc2 = am.account_associates(account2.id)
        # Validate
        self.assertEqual(len(assocs_acc1), 1, 
                         "Did not find the correct amount of associates")
        self.assertEqual(len(assocs_acc2), 1, 
                         "Did not find the correct amount of associates")