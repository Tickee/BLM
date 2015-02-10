from tickee.paymentproviders import manager

class PaymentProvider(object):
    
    @classmethod
    def build_from_info(cls, psp_info):
        """return the correct psp with merchant info in it"""
        psp_klass = manager.lookup_payment_provider_class_by_name(psp_info.provider_type)
        return psp_klass(psp_info)
    
    def __repr__(self):
        return "<%s: using psp_id %s>" % (self.__name__, self.payment_provider_info.id)
    
    def get_provider_info(self):
        return self.payment_provider_info
    
    # Payment provider creation
    
    def __init__(self, payment_provider_info):
        """Creates a payment provider by associating it with the merchant
        information"""
        self.payment_provider_info = payment_provider_info
    
    # Checkout handling
    
    def checkout_order(self, order):
        """negotiates a transaction request for the order with the payment provider"""
    
    # Notification handling
    
    def get_order(self):
        """Returns the order related to the notification"""
    
    def handle_notification(self, context):
        """Handles the notification and returns payment status"""
    
    def generate_success_response(self, context):
        """Generates the response context to answer a successful request"""
    
    def generate_failure_response(self, context): 
        """Generates the response context to answer a failed request"""
    
    def on_shipped(self, order):
        """Handles actions necessary when order has been shipped"""
    
    def transaction_information(self, context, order):
        """Retrieves information about the transaction using either the
        notification context or the order"""