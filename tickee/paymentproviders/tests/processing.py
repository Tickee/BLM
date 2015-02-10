from tickee.accounts.processing import create_account
from tickee.paymentproviders.processing import get_or_create_transaction_statistic, increment_transaction_count
from tickee.tests import BaseTestCase
from tickee.users.processing import create_user
import datetime

class TransactionStatisticsTestCase(BaseTestCase):
    
    def setUp(self):
        super(TransactionStatisticsTestCase, self).setUp()
        self.user = create_user("user@example.com")
        self.account = create_account("accountname", "email")
        
    # get_or_create_transaction_statistic(account, year, month)
    
    def test_create_transaction_statistic(self):
        stat = get_or_create_transaction_statistic(self.account)
        self.assertEqual(stat.year, datetime.date.today().year)
        self.assertEqual(stat.month, datetime.date.today().month)
        
    def test_duplicate_creation(self):
        stat1 = get_or_create_transaction_statistic(self.account)
        stat2 = get_or_create_transaction_statistic(self.account)
        self.assertEqual(stat1, stat2)
    
    # increment_transaction_count(account)
    
    def test_increment_account(self):
        increment_transaction_count(self.account, 5)
        stats = get_or_create_transaction_statistic(self.account)
        self.assertEqual(stats.amount, 5)
    
    