
def notification_history_request_t(serial_nr):
    return """<?xml version="1.0" encoding="UTF-8"?><notification-history-request xmlns="http://checkout.google.com/schema/2">
  <serial-number>%s</serial-number>
</notification-history-request>""" % serial_nr

def notification_acknowledge_t(serial_nr):
    return """<notification-acknowledgment xmlns="http://checkout.google.com/schema/2" 
    serial-number="%s" />""" % serial_nr
    
    
def charge_and_ship_t(order):
    return """<?xml version="1.0" encoding="UTF-8"?>
<charge-and-ship-order xmlns="http://checkout.google.com/schema/2" google-order-number="{google_order_nr}">
    <amount currency="{currency}">{amount}</amount>
    <tracking-data-list />
</charge-and-ship-order>""".format(google_order_nr=order.meta.get('google_order_nr'),
                                   amount=float(order.get_total())/100,
                                   currency='USD')