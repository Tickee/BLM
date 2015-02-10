from base64 import b64encode
from gchecky.controller import Controller as OriginalController, ControllerContext, LibraryError, gmodel, gxml, \
    html_escape

class xml_order(object):
    order = None
    signature = None
    url = None #Set by application before calling .html()
    button = None
    xml = None

    def html(self):
        """
        Return the html form containing two required hidden fields
        and the submit button in the form of Google Checkout button image.
        """
        return """
               <form method="post" action="%s">
                   <input type="image" src="%s" alt="Google Checkout" />
               </form>
               """ % (html_escape(self.url), html_escape(self.button))


class ControllerLevel_2(OriginalController):
    """Name changed to use private methods easily"""
    def prepare_server_order(self, order, order_id=None, diagnose=False):
        oo = xml_order()
        oo.url = None #Application defined post back
        oo.order = order
        oo.button = self.get_checkout_button_url(diagnose)
        oo.submit = lambda diagnose=False: self.post_cart(oo.order, diagnose)
        return oo


    def _send_xml(self, msg, context, diagnose):
        """
        The helper method that submits an xml message to GC.
        """
        context.diagnose = diagnose
        url = getattr(context, 'url', self.get_order_processing_url(diagnose))
        context.url = url
        import urllib2
        req = urllib2.Request(url=url, data=msg)
        req.add_header('Authorization',
                       'Basic %s' % (b64encode('%s:%s' % (self.vendor_id,
                                                          self.merchant_key)),))
        req.add_header('Content-Type', ' application/xml; charset=UTF-8')
        req.add_header('Accept', ' application/xml; charset=UTF-8')
        try:
            self.__call_handler('on_xml_sending', context=context)
            response = urllib2.urlopen(req).read()
            print response
            self.__call_handler('on_xml_sent', context=context)
            return response
        except urllib2.HTTPError, e:
            error = e.fp.read()
            print 'Error in urllib2.urlopen: %s' % (error,)


    def __process_message_result(self, response_xml, context):
        try:
            return super(ControllerLevel_2, self).__process_message_result(response_xml, context)
        except LibraryError as e:
            try:
                doc = gxml.Document.fromxml(response_xml)
                if doc.__class__ == gmodel.checkout_redirect_t:
                    return doc
            except:
                raise

    def post_cart(self, cart_t, diagnose=False):
        context = ControllerContext(outgoing=True)
        context.url = self.get_server_post_cart_url(diagnose)
        return self.send_message(cart_t, context=context, diagnose=diagnose)


ServerCartController = ControllerLevel_2