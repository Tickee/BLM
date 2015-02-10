from tickee.orders.manager import lookup_order_by_payment_key
from tickee.paymentproviders.manager import lookup_payment_provider_class_by_name
import logging
import tickee.exceptions as ex

tlogger = logging.getLogger('technical')

class PaymentProvider(object):
    
    @classmethod
    def build_from_info(cls, psp_info):
        """ Returns the correct psp with merchant info in it """
        psp_klass = lookup_payment_provider_class_by_name(psp_info.provider_type)
        return psp_klass(psp_info)        
    
    def __init__(self, psp_info):
        """ initializes the payment provider interface with a configuration """
        self.psp_info = psp_info
    
    def __repr__(self):
        return "<%s: with psp_id %s>" % (self.name, self.get_provider_info().id)
    
    
    
    
    # -- externally available methods------------------------------------------
    
    
    
    
    def checkout_order(self, order):
        """ Performs a checkout for the order """
        try:
            payment_url = self.perform_checkout(order)
        except:
            tlogger.critical('Failed starting a transaction for order with order_key %s and payment_key %s'\
                             % (order.order_key, order.payment_key))
            return None
        else:
            return dict(payment_url=payment_url,
                        provider=self.name)
    
    def handle_notification(self, context):
        """ Contacts the payment service provider to fullfill notification. """
        notification = self.fetch_notification(context)
        # find related order
        payment_key = self.get_payment_code(context, notification)
        order = lookup_order_by_payment_key(payment_key)
        self.store_order(order)
        # validate if this is correct psp to handle order
        self.assert_correct_psp_used(order)
        # handle possible error with notification content
        self.assert_not_an_error(notification)
        # interpret notification status
        status = self.read_status(notification)
        if status is None:
            tlogger.warn('received unknown status from psp %s.' % self.name)
        # save the notification in the database
        self.save_notification_for_order(notification, order)
    
    def get_provider_info(self):
        """ Returns the payment service provider info object """
        return self.psp_info
    
    
    
    
    
    
    # -- internal generic logic -----------------------------------------------
    
    
    
    
    
    def store_order(self, order):
        self.order = order
        
    def get_order(self):
        return self.order
    
    def assert_correct_psp_used(self, order):
        """ Raises an error if an incorrect PSP configuration is used. """
        if not order.payment_provider_id == self.get_provider_info().id:
            tlogger.error("wrong psp id (%s) given for order %s: expected %s" % (self.get_provider_info().id,
                                                                                 order.id,
                                                                                 order.payment_provider_id))
            raise ex.PaymentError("wrong paymentprovider used.")
    
    def assert_not_an_error(self, notification):
        """ Raises an error if the received notification content contained an
        error message """
        if self.is_error(notification):
            tlogger.error("received error for ")
            raise ex.PaymentError("received error from PSP")
    
    def save_notification(self, notification, order):
        """ Saves the notification in the database """
        notification_name = "notif_%s" % self.read_status(notification)
        order.meta[notification_name] = self.as_json(notification) 
    
    def may_charge_handling_fee(self, account):
        """ Returns True if account is able to charge a handling fee """
        return account.subscription.get_feature('service_fee_enabled')
    
    def get_shopping_cart_items(self, order):
        """ Returns a list of psp specific cart items, might contain handling fee, 
        depending on subscription type """ 
        items = list()
        handling_fee = 0
        # add ticket orders
        for ticketorder in order.ordered_tickets:
            item = self.ticketorder_to_cart_item(ticketorder)
            items.append(item)
            handling_fee += ticketorder.ticket_type.get_handling_fee() * ticketorder.amount / 100.0
        # add handling fee
        if self.may_charge_handling_fee(order.account):
            items.append(self.handling_fee_to_cart_item(handling_fee))
        return items
    
    def is_test(self):
        """ Returns true if the payment service provider information is for testing """
        return self.get_provider_info().get_info('is_test')
    
    
    
    
    
    # ---- methods to implement -----------------------------------------------
    
    
    
    
    
    def perform_checkout(self, order):
        """ Calls the payment service provider and returns the payment url """ 
        raise NotImplementedError
    
    def ticketorder_to_cart_item(self, ticketorder):
        """ Returns a cart item representing the ticketorder """
        raise NotImplementedError
    
    def handling_fee_to_cart_item(self, amount):
        """ Returns a cart item representing the handling fee """
        raise NotImplementedError
    
    def fetch_notification(self, context):
        """ Understands the notification and fetches its content from the PSP """ 
        raise NotImplementedError
    
    def get_payment_key(self, context, notification):
        """ Returns the payment key related to the notification """
        raise NotImplementedError
    
    def is_error(self, notification):
        """ Returns True if the psp returned an error message instead of the content """
        raise NotImplementedError
    
    def log_notification(self, notification):
        """ Logs the notification as a debug message to the technical logger """
        raise NotImplementedError
    
    def as_json(self, notification):
        """ Transforms the notification to a JSON representation """
        raise NotImplementedError
    
    def read_status(self, notification):
        """ Interprets the notification content and returns the status """
        raise NotImplementedError


