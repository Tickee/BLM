
from tickee.db.models.order import Order
from tickee.db.models.ticketorder import TicketOrder
from tickee.tests import BaseTestCase
from tickee.tickets.manager import tickets_from_order
from tickee.tickets.tasks import create_tickets
import sqlahelper

Session = sqlahelper.get_session()

class TicketManagerTestCase(BaseTestCase):
    
    def setUp(self):
        super(TicketManagerTestCase, self).setUp()
        self.order = Order(None, None)
        Session.add(self.order)
        Session.flush()
        ticketorder = TicketOrder(self.order.id, None, 5)
        Session.add(ticketorder)
        Session.flush()

    # tickets_from_order
    
    def test_uncreated_tickets_from_order(self):
        self.assertEqual(len(tickets_from_order(self.order)),
                         0)
    
    def test_created_tickets_from_order(self):
        create_tickets(self.order)
        self.assertEqual(len(tickets_from_order(self.order)),
                         5)
        
    def test_created_double_tickets_from_order(self):
        create_tickets(self.order)
        self.assertEqual(len(tickets_from_order(self.order)),
                         5)