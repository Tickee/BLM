from tickee.accounts.processing import create_account
from tickee.subscriptions.models import Subscription, FREE, PREMIUM, PREMIUMPRO
from tickee.subscriptions.plans import FreeSubscriptionPlan, PremiumSubscriptionPlan, PremiumProSubscriptionPlan
from tickee.tests import BaseTestCase
import datetime

class SubscriptionModelTestCase(BaseTestCase):
    
    def setUp(self):
        super(SubscriptionModelTestCase, self).setUp()
        self.account = create_account("accountname", "email")
        
    # get_subscription
    
    def test_create_free_subscription(self):
        sub = Subscription(FREE)
        self.assertIsInstance(sub.get_subscription(), FreeSubscriptionPlan)
    
    def test_create_premium_subscription(self):
        sub = Subscription(PREMIUM)
        self.assertIsInstance(sub.get_subscription(), PremiumSubscriptionPlan)
    
    def test_create_premiumpro_subscription(self):
        sub = Subscription(PREMIUMPRO)
        self.assertIsInstance(sub.get_subscription(), PremiumProSubscriptionPlan)
        
    # is_active
    
    def test_active_subscription(self):
        sub = Subscription(PREMIUM)
        after_today = datetime.date.today() + datetime.timedelta(days=1)
        sub.end_date = after_today
        self.assertTrue(sub.is_active())
        
    def test_inactive_subscription(self):
        sub = Subscription(PREMIUM)
        before_today = datetime.date.today() - datetime.timedelta(days=1)
        sub.end_date = before_today
        self.assertFalse(sub.is_active())
    
    def test_today_is_end_date(self):
        sub = Subscription(PREMIUM)
        today = datetime.date.today()
        sub.end_date = today
        self.assertTrue(sub.is_active())
    
    def test_free_always_valid(self):
        sub = Subscription(FREE)
        today = datetime.date.today() - datetime.timedelta(days=1)
        sub.end_date = today
        self.assertTrue(sub.is_active())
        
    # get_feature
    
    def test_get_transaction_amount(self):
        sub = Subscription(FREE)
        self.assertEqual(sub.get_feature('transactions_per_month'), 
                         FreeSubscriptionPlan.transactions_per_month)