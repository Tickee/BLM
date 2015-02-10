from tickee import logic
from tickee.db.models.tickettype import TicketType
import tests
class CreateTicketTypeTest(tests.BaseTestCase):
    
    def setUp(self):
        super(CreateTicketTypeTest, self).setUp()
        cm = logic.CurrencyManager()
        self.currency = cm.create_currency("EUR", "Euro") 
    # init
    
    def test_create_tickettype(self):
        # Test
        tickettype = TicketType("name", 15, "EUR", 10)
        # Validate
        self.assertIsInstance(tickettype, TicketType)
        self.assertEqual(tickettype.name, "name")
        self.assertEqual(tickettype.get_price(), 15)
        self.assertEqual(tickettype.currency_id, "EUR")