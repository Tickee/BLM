'''
Created on 30-aug-2011

@author: kevin
'''
from lxml import etree
import md5

class XMLStructure(object):
    
    def __init__(self, node_name, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, unicode(value))
        self.root = etree.Element(node_name)
    def __getattr__(self, name):
        return ""
    def get_xml_node(self):
        return self.root
    def to_string(self):
        return etree.tostring(self.root, pretty_print=True)

class Status(XMLStructure):
    def __init__(self, merchant, transaction):
        super(Status, self).__init__("status")
        self.merchant = merchant
        self.transaction = transaction
        self._create_xml()
    def _create_xml(self):
        self.root.append(self.merchant.get_xml_node())
        self.root.append(self.transaction.get_xml_node())

class CheckoutTransaction(XMLStructure):
    def __init__(self, merchant, customer, customerdelivery, transaction,
                 checkoutshoppingcart, customfields=None):
        super(CheckoutTransaction, self).__init__("checkouttransaction")
        self.merchant = merchant
        self.customer = customer
        self.customerdelivery = customerdelivery
        self.checkoutshoppingcart = checkoutshoppingcart
        self.transaction = transaction
        self.customfields = customfields
        self._create_xml()
        self._calculate_signature()
    def _create_xml(self):
        self.root.append(self.merchant.get_xml_node())
        self.root.append(self.customer.get_xml_node())
        if self.customerdelivery:
            self.root.append(self.customerdelivery.get_xml_node())
        self.root.append(self.checkoutshoppingcart.get_xml_node())
        self.root.append(self.transaction.get_xml_node())
        if self.customfields:
            self.root.append(self.customfields.get_xml_node())
        
    def _calculate_signature(self):
        # hash data
        m = md5.new()
        unhashed = self.root.find('transaction').find('amount').text\
                 + self.root.find('transaction').find('currency').text\
                 + self.root.find('merchant').find('account').text\
                 + self.root.find('merchant').find('site_id').text\
                 + self.root.find('transaction').find('id').text
                   
        m.update(unhashed)
        etree.SubElement(self.root, "signature").text = m.hexdigest()

class Transaction(XMLStructure):
    def __init__(self, **kwargs):
        super(Transaction, self).__init__("transaction", **kwargs)
        self._create_xml()
    def _create_xml(self):
        etree.SubElement(self.root, "id").text = self.id
        etree.SubElement(self.root, "currency").text = self.currency
        etree.SubElement(self.root, "amount").text = self.amount
        etree.SubElement(self.root, "description").text = self.description
        etree.SubElement(self.root, "var1").text = self.var1
        etree.SubElement(self.root, "var2").text = self.var2
        etree.SubElement(self.root, "var3").text = self.var3
#        etree.SubElement(self.root, "items").text = self.items
#        etree.SubElement(self.root, "manual").text = self.manual
        
        
class Merchant(XMLStructure):
    def __init__(self, **kwargs):
        super(Merchant, self).__init__("merchant", **kwargs)
        self._create_xml()
    def _create_xml(self):
        etree.SubElement(self.root, "account").text = self.account
        etree.SubElement(self.root, "site_id").text = self.site_id
        etree.SubElement(self.root, "site_secure_code").text = self.site_secure_code
        etree.SubElement(self.root, "notification_url").text = self.notification_url
        etree.SubElement(self.root, "cancel_url").text = self.cancel_url
        etree.SubElement(self.root, "redirect_url").text = self.redirect_url
        etree.SubElement(self.root, "close_window").text = self.close_window

class Customer(XMLStructure):
    def __init__(self, **kwargs):
        super(Customer, self).__init__("customer", **kwargs)
        self._create_xml()
    def _create_xml(self):
        etree.SubElement(self.root, "locale").text = self.locale
        etree.SubElement(self.root, "ipaddress").text = self.ipaddress
        etree.SubElement(self.root, "forwardedip").text = self.forwardedip
        if self.firstname == "None":
            self.firstname = ""
        etree.SubElement(self.root, "firstname").text = self.firstname
        if self.lastname == "None":
            self.lastname = ""
        etree.SubElement(self.root, "lastname").text = self.lastname
        etree.SubElement(self.root, "address1").text = self.address1
        etree.SubElement(self.root, "address2").text = self.address2
        etree.SubElement(self.root, "housenumber").text = self.housenumber
        etree.SubElement(self.root, "zipcode").text = self.zipcode
        etree.SubElement(self.root, "city").text = self.city
        etree.SubElement(self.root, "country").text = self.country
        etree.SubElement(self.root, "phone").text = self.phone
        etree.SubElement(self.root, "email").text = self.email

class CustomerDelivery(XMLStructure):
    def __init__(self, **kwargs):
        super(CustomerDelivery, self).__init__("customer-delivery", **kwargs)
        self._create_xml()
    def _create_xml(self):
        etree.SubElement(self.root, "firstname").text = self.firstname
        etree.SubElement(self.root, "lastname").text = self.lastname
        etree.SubElement(self.root, "address1").text = self.address1
        etree.SubElement(self.root, "address2").text = self.address2
        etree.SubElement(self.root, "housenumber").text = self.housenumber
        etree.SubElement(self.root, "zipcode").text = self.zipcode
        etree.SubElement(self.root, "city").text = self.city
        etree.SubElement(self.root, "country").text = self.country
        etree.SubElement(self.root, "phone").text = self.phone
        
class CheckoutShoppingCart(XMLStructure):
    def __init__(self, shoppingcart, checkoutflowsupport=None):
        super(CheckoutShoppingCart, self).__init__("checkout-shopping-cart")
        self.shoppingcart = shoppingcart
        self.checkoutflowsupport = checkoutflowsupport
        self._create_xml()
    def _create_xml(self):
        self.root.append(self.shoppingcart.get_xml_node())
        if self.checkoutflowsupport:
            self.root.append(self.checkoutflowsupport.get_xml_node())
        
class ShoppingCart(XMLStructure):
    def __init__(self, item_list):
        super(ShoppingCart, self).__init__("shopping-cart")
        self.item_list = item_list
        self._create_xml()
    def _create_xml(self):
        items = etree.SubElement(self.root, "items")
        for item in self.item_list:
            items.append(item.get_xml_node())

class ShoppingCartItem(XMLStructure):
    def __init__(self, **kwargs):
        super(ShoppingCartItem, self).__init__("item", **kwargs)
        self._create_xml()
    def _create_xml(self):
        etree.SubElement(self.root, "item-name").text = self.item_name
        etree.SubElement(self.root, "item-description").text = self.item_description
        etree.SubElement(self.root, "unit-price", attrib={'currency':'EUR'}).text = self.unit_price
        etree.SubElement(self.root, "quantity").text = self.quantity
        etree.SubElement(self.root, "merchant-item-id").text = self.merchant_item_id
        
class CheckoutFlowSupport(XMLStructure):
    def __init__(self, **kwargs):
        super(CheckoutFlowSupport, self).__init__("checkout-flow-support", **kwargs)
        self._create_xml()
    def _create_xml(self):
        merchantcheckoutflowsupport = etree.SubElement(self.root, "merchant-checkout-flow-support")
        shippingmethods = etree.SubElement(merchantcheckoutflowsupport, "shipping-methods")
        flatrate = etree.SubElement(shippingmethods, "flat-rate-shipping", attrib={'name':"Tickee e-mail (no address needed)"})
        etree.SubElement(flatrate, "price", attrib={'currency': "EUR"}).text = "0"
        