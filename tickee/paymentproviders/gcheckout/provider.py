from lxml import etree
from tickee.orders.manager import lookup_order_by_payment_key
from tickee.paymentproviders import TransactionInformation, UserInformation, elem2dict
from tickee.paymentproviders.gcheckout.controller import ServerCartController
from tickee.paymentproviders.states import PSP_NEW_ORDER, PSP_RISK_ASSESSMENT, PSP_STATE_CHANGED, PSP_READY_FOR_PAYMENT, \
    PSP_PAYED, PSP_REFUNDED, PSP_CHARGEBACK_REQUESTED
import base64
import gchecky.model as gmodel
import logging
import marshalling
import requests
import urlparse
import tickee.exceptions as ex
#from tickee.orders.paymentproviders import PaymentProvider

GOOGLECHECKOUT_NAMESPACE = "http://checkout.google.com/schema/2"
GOOGLECHECKOUT = "{%s}" % GOOGLECHECKOUT_NAMESPACE

blogger = logging.getLogger('blm.payment')
tlogger = logging.getLogger('technical')

class GoogleCheckoutPaymentProvider(object):
    
    required_configuration_fields = ['merchant_id', 'merchant_key', 'is_sandbox', 'currency']
    
    # Payment provider creation
    
    def __init__(self, payment_provider_info):
        """Creates a payment provider by associating it with the merchant
        information"""
        self.payment_provider_info = payment_provider_info
        self.order = None
    
    def get_provider_info(self):
        return self.payment_provider_info
    
    def get_name(self):
        return "goog-co"
    
    # Checkout handling
    
    def checkout_order(self, order):
        """negotiates a transaction request for the order with the payment provider"""
        payment_info = self.perform_checkout_request(order)
        return payment_info
    
    # Notification handling
    
    def get_order(self):
        """Returns the order related to the notification"""
        return self.order
    
    def handle_notification(self, context):
        """Handles the notification and returns payment status"""
        serial_nr = self._get_serial_number(context)
        self.notification = self._fetch_notification(serial_nr)
        # view notif
        tlogger.debug('GOOGLE notification: %s' % self.notification)
        # store notification in system
        self.store_order(self.notification)
        # validate if psp matches order.
        if self.order.payment_provider_id != self.payment_provider_info.id:
            blogger.critical("wrong psp id (%s) given for order %s: expected %s" % (self.payment_provider_info.id,
                                                                                    self.order.id,
                                                                                    self.order.payment_provider_id))
            raise ex.PaymentError("wrong paymentprovider used.")
        # translate notification
        tag = self.notification.tag.rsplit("}", 1)[-1]
        if tag == 'new-order-notification':
            self.order.meta['new_order_raw'] = elem2dict(self.notification)
            self.order.meta['google_order_nr'] = self._get_google_order_number(self.notification)
            return PSP_NEW_ORDER
        elif tag == 'risk-information-notification':
            return PSP_RISK_ASSESSMENT
        elif tag == 'order-state-change-notification':
            return PSP_STATE_CHANGED
        elif tag == 'authorization-amount-notification':
            return PSP_READY_FOR_PAYMENT
        elif tag == 'charge-amount-notification':
            self.order.meta['payed'] = elem2dict(self.notification)
            return PSP_PAYED
        elif tag == 'refund-amount-notification':
            return PSP_REFUNDED
        elif tag == 'chargeback-amount-notification':
            return PSP_CHARGEBACK_REQUESTED
        else:
            tlogger.warn('received unknown status from psp %s: %s' % (self.get_name(), tag))
    
    def generate_success_response(self, context):
        """Generates the response context to answer a successful request"""
        serial_nr = self._get_serial_number(context)
        return marshalling.notification_acknowledge_t(serial_nr)
        
    def generate_failure_response(self, context): 
        """Generates the response context to answer a failed request"""
        return "ERROR"
        
    # Notification handlers
    
    def store_order(self, root):
        """
        Stores the order object related to the notification
        """
        merchant_private_data_node = root.find(GOOGLECHECKOUT+'order-summary')\
                                         .find(GOOGLECHECKOUT+'shopping-cart')\
                                         .find(GOOGLECHECKOUT+'merchant-private-data')
        payment_key = merchant_private_data_node.text
        self.order = lookup_order_by_payment_key(payment_key)
    
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
            customer = root.find(GOOGLECHECKOUT+"order-summary")\
                           .find(GOOGLECHECKOUT+"buyer-shipping-address")
            u_info = UserInformation()
            u_info.first_name = customer.find(GOOGLECHECKOUT+"structured-name")\
                                        .find(GOOGLECHECKOUT+"first-name").text
            u_info.last_name = customer.find(GOOGLECHECKOUT+"structured-name")\
                                       .find(GOOGLECHECKOUT+"last-name").text
            u_info.email = customer.find(GOOGLECHECKOUT+"email").text
            return u_info
    
    # Charge order
    
    def charge_order(self, order):
        charge_amount_notification = self.perform_charge_order_request(order)
        if charge_amount_notification.tag == GOOGLECHECKOUT+'error':
            error_message = charge_amount_notification.find(GOOGLECHECKOUT+'error-message').text
            tlogger.error('problem with charge order %s: %s ' % (order.id, 
                                                                 error_message))
        
        
    def perform_charge_order_request(self, order):
        data = marshalling.charge_and_ship_t(order)
        tlogger.debug("Sending: %s to %s" % (data, self._get_notification_history_url()))
        response = requests.post(self._get_order_processing_url(), data=data, auth=self._get_auth(),
                                 headers=self._get_headers())
        return etree.fromstring(response.content)
    
    # Internal
    
    def _get_google_order_number(self, root):
        """retrieves the order number from the notification"""
        google_order_nr_node = root.find(GOOGLECHECKOUT+'google-order-number')
        return google_order_nr_node.text
    
    def _get_serial_number(self, context):
        """retrieves the serial number from the context"""
        qs_dct = urlparse.parse_qs(context.get('message'))
        return qs_dct.get('serial-number')[0]
    
    def _fetch_notification(self, serial_nr):
        """retrieves the notification from GC"""
        data = marshalling.notification_history_request_t(serial_nr)
        tlogger.debug("Sending: %s to %s" % (data, self._get_notification_history_url()))
        response = requests.post(self._get_notification_history_url(), data=data, auth=self._get_auth(),
                                 headers=self._get_headers())
        return etree.fromstring(response.content)
    
    def perform_checkout_request(self, order):
        cart = self._get_cart(order)
        controller = self._get_controller()
        prepared = controller.prepare_server_order(cart)
        sent_order = prepared.submit()
        return dict(payment_url=sent_order.redirect_url,
                    provider="Google Checkout")
    
    # authentication
    
    def _get_auth(self):
        return (self.payment_provider_info.get_info('merchant_id'), 
                self.payment_provider_info.get_info('merchant_key'))
    
    def _get_headers(self):
        decoded_auth = "%s:%s" % (self.payment_provider_info.get_info('merchant_id'),
                                  self.payment_provider_info.get_info('merchant_key'))
        return {'Content-Type': 'application/xml; charset=UTF-8',
                'Accept': 'application/xml; charset=UTF-8',
                'Authorization': "Basic %s" % base64.b64encode(decoded_auth)}
    
    # urls
    
    def _get_notification_history_url(self):
        if self.payment_provider_info.get_info('is_sandbox'):
            return "https://sandbox.google.com/checkout/api/checkout/v2/reports/Merchant/%s"\
                % self.payment_provider_info.get_info('merchant_id')
        else:
            return "https://checkout.google.com/api/checkout/v2/reports/Merchant/%s"\
                % self.payment_provider_info.get_info('merchant_id')
    
    def _get_order_processing_url(self):
        if self.payment_provider_info.get_info('is_sandbox'):
            return "https://sandbox.google.com/checkout/api/checkout/v2/request/Merchant/%s"\
                % self.payment_provider_info.get_info('merchant_id')
        else:
            return "https://checkout.google.com/api/checkout/v2/request/Merchant/%s"\
                % self.payment_provider_info.get_info('merchant_id')
    
    # gchecky
    
    def _get_cart(self, order):
        cart = gmodel.checkout_shopping_cart_t(
                    shopping_cart = gmodel.shopping_cart_t(
                        items = self._get_items(order),
                        merchant_private_data = order.payment_key),
                    checkout_flow_support = gmodel.checkout_flow_support_t(
                        request_buyer_phone_number = True))
        return cart
        
    def _get_items(self, order):
        items = []
        handling_fee = 0
        for ticketorder in order.get_ticketorders():
            # tickets w/o handling fee                
            items.append(gmodel.item_t(
                name = ticketorder.ticket_type.name + ' ticket',
                description = ticketorder.ticket_type.get_description() or "",
                unit_price = gmodel.price_t(
                    value = ticketorder.ticket_type.get_price() / 100.0,
                    currency = ticketorder.ticket_type.currency_id,
                ),
                quantity = ticketorder.amount))
            # remember handling fee
            handling_fee += ticketorder.ticket_type.get_handling_fee() * ticketorder.amount / 100.0
        
        if order.account.subscription.get_feature('service_fee_enabled'):
            # add handling fee total
            items.append(gmodel.item_t(
                name = 'Handling fee',
                description = "",
                unit_price = gmodel.price_t(
                    value = handling_fee,
                    currency = ticketorder.ticket_type.currency_id,
                ),
                quantity = 1))
        
        
        return items
    
    def _get_controller(self):
        controller = ServerCartController(
                        vendor_id = unicode(self.payment_provider_info.get_info('merchant_id')),
                        merchant_key = unicode(self.payment_provider_info.get_info('merchant_key')),
                        is_sandbox = self.payment_provider_info.get_info('is_sandbox'),
                        currency = self.payment_provider_info.get_info('currency'))
        return controller