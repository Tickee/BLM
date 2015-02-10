from tickee.accounts.processing import create_account
from tickee.db.models.order import Order
from tickee.orders.processing import start_order
from tickee.paymentproviders import UserInformation
from tickee.paymentproviders.tasks import update_user_information
from tickee.tests import BaseTestCase
from tickee.users.processing import create_user
import sqlahelper
import tickee.exceptions as ex

Session = sqlahelper.get_session()

class PaymentProviderTasksTestCase(BaseTestCase):
    
    def setUp(self):
        super(PaymentProviderTasksTestCase, self).setUp()
        self.account = create_account("accountname", "email")
        self.user = create_user("email@example.com")
        self.user2 = create_user("email2@example.com")
        self.order = start_order(self.user, self.account)

    # update_user_information(order, userinfo)
    
    def test_update_user_email(self):
        userinfo = UserInformation()
        userinfo.email = "email3@example.com"
        update_user_information(self.order, userinfo)
        self.assertEqual(self.user.email, userinfo.email)
    
    def test_update_user_duplicate_email(self):
        """ it is possible that there is another user with the same email address """
        userinfo = UserInformation()
        userinfo.email = "email2@example.com"
        update_user_information(self.order, userinfo)
        self.assertNotEqual(self.user.email, userinfo.email)