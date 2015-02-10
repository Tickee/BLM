from tickee.accounts.processing import create_account
from tickee.paymentproviders.processing import get_or_create_transaction_statistic
from tickee.subscriptions.models import Subscription, FREE, PREMIUMPRO
from tickee.subscriptions.permissions import require_available_transactions, has_available_transactions
from tickee.subscriptions.plans import FreeSubscriptionPlan
from tickee.tests import BaseTestCase
import datetime
import tickee.exceptions as ex

class SubscriptionModelTestCase(BaseTestCase):
    
    def setUp(self):
        super(SubscriptionModelTestCase, self).setUp()
        self.account = create_account("accountname", "email")
        self.account.subscription = Subscription(FREE)
        self.today = datetime.date.today()
        
    # has_available_transactions(account)
    
    def test_available_transactions_left(self):
        stat = get_or_create_transaction_statistic(self.account)
        stat.amount = FreeSubscriptionPlan.transactions_per_month - 1
        self.assertTrue(has_available_transactions(self.account))
        
    def test_all_transactions_used_up(self):
        stat = get_or_create_transaction_statistic(self.account)
        stat.amount = FreeSubscriptionPlan.transactions_per_month
        self.assertFalse(has_available_transactions(self.account))
    
    def test_more_than_all_transactions_used_up(self):
        stat = get_or_create_transaction_statistic(self.account)
        stat.amount = FreeSubscriptionPlan.transactions_per_month + 1
        self.assertFalse(has_available_transactions(self.account))            
    
    def test_unlimited_transactions(self):
        account = create_account("account2", "email")
        account.subscription = Subscription(PREMIUMPRO)
        self.assertTrue(has_available_transactions(account))
    
    # require_available_transactions(account)
    
    def test_available_transactions_left_require(self):
        stat = get_or_create_transaction_statistic(self.account)
        stat.amount = FreeSubscriptionPlan.transactions_per_month - 1
        self.assertIsNone(require_available_transactions(self.account))
        
    def test_all_transactions_used_up_require(self):
        stat = get_or_create_transaction_statistic(self.account)
        stat.amount = FreeSubscriptionPlan.transactions_per_month
        self.assertRaises(ex.SubscriptionError, require_available_transactions, self.account)
    
    def test_more_than_all_transactions_used_up_require(self):
        stat = get_or_create_transaction_statistic(self.account)
        stat.amount = FreeSubscriptionPlan.transactions_per_month + 1
        self.assertRaises(ex.SubscriptionError, require_available_transactions, self.account)    