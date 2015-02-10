from lxml import etree
from tickee.orders.manager import lookup_order_by_payment_key
from tickee.paymentproviders import elem2dict, UserInformation, TransactionInformation
from tickee.paymentproviders.states import PSP_NEW_ORDER, PSP_PAYED, PSP_UNKNOWN, PSP_CANCELLED
import logging
import marshalling
import requests
import sqlahelper
import tickee.exceptions as ex

GOOGLECHECKOUT_NAMESPACE = "http://checkout.google.com/schema/2"
GOOGLECHECKOUT = "{%s}" % GOOGLECHECKOUT_NAMESPACE

blogger = logging.getLogger('blm.payment')
tlogger = logging.getLogger('technical')

Session = sqlahelper.get_session()

class FastCheckoutPaymentProvider(object):
    
    required_configuration_fields = ['account_id', 'site_id', 'site_secure_code', 'is_test', 'currency']
    
    # Payment provider creation
    
    def __init__(self, payment_provider_info):
        """Creates a payment provider by associating it with the merchant
        information"""
        self.payment_provider_info = payment_provider_info
        self.order = None
        self.notification = None
        
    def get_name(self):
        return "msp-fc"
    
    def get_provider_info(self):
        return self.payment_provider_info
    
    # Checkout handling
    
    def checkout_order(self, order):
        """negotiates a transaction request for the order with the payment provider"""
        payment_info = self.perform_checkout_request(order)
        return payment_info
    
    def perform_checkout_request(self, order):
        # create checkout request
        checkout_request = self._build_checkout_request(order)
        tlogger.debug("Request to payment provider:\n%s" % checkout_request)
        # issue request
        response = requests.post(self._get_url(), checkout_request)
        tlogger.debug("Response from payment provider:\n%s" % response.content)
        # parse api response
        root = etree.fromstring(response.content)
        result = root.get('result')
        # successful checkout request
        if result == "ok":
            payment_url = root.find('transaction').find('payment_url').text
            return dict(payment_url=payment_url,
                        provider="Multisafepay")
        # failed checkout request
        else:
            tlogger.error('Failed starting a transaction for order with order_key %s and payment_key %s' % (order.order_key,
                                                                                                            order.payment_key))
            tlogger.error('Request:\n%s' % checkout_request)
            tlogger.error('Response:\n%s' % response.content)
    
    # Notification handling
    
    def get_order(self):
        """Returns the order related to the notification"""
        return self.order
    
    def handle_notification(self, context):
        """Handles the notification and returns payment status"""
        # fetch transactionid == payment_key
        try:
            transactionid = context.get('params').get('transactionid')[0]
        except:
            tlogger.error('received MSP notification with no transactionid.')
            return PSP_UNKNOWN
        # store order related to transaction
        self.order = lookup_order_by_payment_key(transactionid)
        # validate if psp matches order.
        if self.order.payment_provider_id != self.payment_provider_info.id:
            blogger.critical("wrong psp id (%s) given for order %s: expected %s" % (self.payment_provider_info.id,
                                                                                    self.order.id,
                                                                                    self.order.payment_provider_id))
            raise ex.PaymentError("wrong paymentprovider used.")
        # retrieve transaction info from psp
        status, self.notification = self._fetch_transaction_information(self.order)
        # store notification information 
        if status == 'completed':
            self.order.meta['completed'] = elem2dict(self.notification)
            Session.flush()
            return PSP_PAYED
        elif status == 'initialized':
            self.order.meta['init'] = elem2dict(self.notification)
            Session.flush()
            return PSP_NEW_ORDER
        elif status == 'void' or status == 'declined':
            self.order.meta['cancelled'] = elem2dict(self.notification)
            Session.flush()
            return PSP_CANCELLED
        else:
            tlogger.warn('received unknown status from psp %s: %s' % (self.get_name(), status))
    
    def _fetch_transaction_information(self, order):
        root = self.perform_status_request(order)
        if root.get('result') != 'error':
            ewallet_status = root.find("ewallet").find("status").text
            return ewallet_status, root
        else:
            blogger.error("msp error received fetching status for order %s" % order.id)
            return 'error', ''
    
    def perform_status_request(self, order):
        status = marshalling.Status(self._tickee_merchant(order), 
                                    self._build_transaction(order))
        tlogger.debug("requesting status update for order %s" % order.id)
        response = requests.post(self._get_url(), status.to_string())
        tlogger.debug("response from Multisafepay:\n%s" % response.content)
        # cache information
        root = etree.fromstring(response.content)
        return root

    def generate_success_response(self, context):
        """Generates the response context to answer a successful request"""
        return "OK"
        
    def generate_failure_response(self, context): 
        """Generates the response context to answer a failed request"""
        return "ERROR"
    
    def transaction_information(self, context, order):
        """Retrieves information about the transaction using either the
        notification context or the order"""
    
    # Transaction information
    
    def get_transaction_information(self):
        if self.notification is not None:
            t_info = TransactionInformation()
            t_info.buyer = self.get_buyer_information()
            return t_info
    
    def get_buyer_information(self):
        """Translates information of the user"""
        # retrieve user information
        if self.notification is not None:
            root = self.notification
            customer = root.find("customer")
            u_info = UserInformation()
            u_info.first_name = customer.find("firstname").text
            u_info.last_name = customer.find("lastname").text
            u_info.email = customer.find("email").text
            return u_info
    
    # Charge order
    
    def charge_order(self, order):
        pass # MSP does not allow manual charging.

    # urls
    
    def _get_url(self):
        if self.payment_provider_info.get_info('is_test'):
            return "https://testapi.multisafepay.com/ewx/"
        else:
            return "https://api.multisafepay.com/ewx/"

    # Request building
    
    def _build_checkout_request(self, order):
        # create empty transaction
        merchant = self._tickee_merchant(order)
        # prepare customer info
        customer = marshalling.Customer(locale="NL_be",
                                        firstname=order.user.first_name,
                                        lastname=order.user.last_name,
                                        email=order.user.email)
        customerdelivery = None
        # prepare shopping cart
        item_list = []
        ticket_count = 0
        handling_fee_amount = 0
        for ticketorder in order.ordered_tickets:
            item = marshalling.ShoppingCartItem(item_name=ticketorder.ticket_type.name + " ticket",
                                                item_description=ticketorder.ticket_type.get_description(),
                                                unit_price=ticketorder.ticket_type.get_price() / 100.0,
                                                quantity=ticketorder.amount,
                                                merchant_item_id=ticketorder.id)
            ticket_count += ticketorder.amount
            handling_fee_amount += ticketorder.ticket_type.get_handling_fee() * ticketorder.amount / 100.0
            item_list.append(item)
        if order.account.subscription.get_feature('service_fee_enabled'):
            # Add Handling fee ShoppingCartItem for each ticket
            handling_fee = marshalling.ShoppingCartItem(item_name="Handling Fee",
                                                        item_description="",
                                                        unit_price=handling_fee_amount,
                                                        quantity=1,
                                                        merchant_item_id=0)
            item_list.append(handling_fee)
        
        shoppingcart = marshalling.ShoppingCart(item_list)
        checkoutflowsupport = marshalling.CheckoutFlowSupport()
        checkoutshoppingcart = marshalling.CheckoutShoppingCart(shoppingcart, checkoutflowsupport)
        # prepare transaction info
        transaction = self._build_transaction(order)
        # prepare checkout
        checkout = marshalling.CheckoutTransaction(
                                    merchant, 
                                    customer, 
                                    customerdelivery, 
                                    transaction,
                                    checkoutshoppingcart).to_string()
        return checkout
    
    def _build_transaction(self, order):
        return marshalling.Transaction(id=order.payment_key,
                                       currency="EUR",
                                       amount=order.get_total(),
                                       description="Tickee Order - %s" % ( order.account.name ))
    
    def _tickee_merchant(self, order):
        return marshalling.Merchant(account=self.payment_provider_info.get_info('account_id'), # "10142991"
                                    site_id=self.payment_provider_info.get_info('site_id'), # "15039"
                                    site_secure_code=self.payment_provider_info.get_info('site_secure_code'), # "434913"
                                    redirect_url="http://tick.ee/account/%s/thanks/%s:%s" % (order.account_id, 
                                                                                             order.order_key, 
                                                                                             order.user_id),
                                    cancel_url="http://tick.ee/account/%s/thanks/%s" % (order.account_id,
                                                                                        order.order_key),
                                    close_window="false")

#class MultiSafepay(PaymentProvider):
#    
#    
#    
#    
#    # Interface methods
#    

##    
#    def transaction_information(self, order_id):
#        """Retrieves user information of a specific order transaction"""
#        order = lookup_order_by_id(order_id)
#        root = self.perform_status_request(order, ignore_cache=False)
#        userinfo = self.user_information(root)
#        info = TransactionInformation()
#        info.set_user(userinfo)
#        return info        
##    
##    def transaction_status(self, order_id):
#        """Retrieves the transaction status of the order."""
#    # Transaction parsing
#    
#        
