from lxml import etree
import logging
import requests
from tickee.exceptions import SubscriptionError

SAASY_URL = "https://api.fastspring.com"

tlogger = logging.getLogger('technical')

def fetch_subscription_details(subscription_ref):
    """ Retrieves subscription details from the Saasy api and returns an etree object containing
    the response. """
    url = SAASY_URL + '/company/tickee/subscription/' + subscription_ref
    tlogger.debug('fetching subscription details: %s' % url)
    r = requests.get(url, auth=('api', 'lleesitzro'))
    # found subscription details
    if r.status_code == 200:
        response = etree.fromstring(r.content)
        return response
        
    # there was a problem retrieving subscription details
    else:
        print r.status_code
        tlogger.error("failed fetching subscription details for subscription reference %s, error code:"\
                      % (subscription_ref, r.status_code))
        raise SubscriptionError("failed fetching subscription details for subscription reference %s" % subscription_ref)
        