import sqlahelper
import tests
import tickee.exceptions as ex
import tickee.logic as logic

Session = sqlahelper.get_session()

class CurrencyTest(tests.BaseTestCase):
    
    # create_account
    
    def test_create_currency(self):
        # Setup
        cm = logic.CurrencyManager()
        # Test
        cm.create_currency("EUR", "Euro")
        
    def test_create_duplicate_currency(self):
        # Setup
        cm = logic.CurrencyManager()
        # Test
        cm.create_currency("EUR", "Euro")
        self.assertRaises(ex.DuplicateCurrencyError, cm.create_currency, 
                          "EUR", "Euro")
        
    # lookup_currency_by_iso
    
    def test_look_up_currency(self):
        # Setup
        cm = logic.CurrencyManager()
        c = cm.create_currency("EUR", "Euro")
        # Test
        currency = cm.lookup_currency_by_iso_code(c.name)
        # Validate
        self.assertEqual(c.name, currency.name, 
                         "Names of currency do not match")
        self.assertEqual(c.full_name, currency.full_name, 
                         "Full names of currency do not match")