from sqlalchemy.exc import IntegrityError
from tickee.core.currency.models import Currency
import sqlahelper
import tickee.exceptions as ex



Session = sqlahelper.get_session()

def create_currency(iso_code, full_name):
    """
    Adds a new currency to the system.
    
    Args:
        iso_code:
            The ISO 4217 code of the currency, 
            see http://en.wikipedia.org/wiki/ISO_4217
        full_name:
            The fully written out name of the currency according to 
            the ISO 4217 specification.
            
    Returns:
        The newly created ``Currency`` object.
        
    Raises:
        DuplicateCurrencyError:
            The currency with that ISO code already exists.
    """
    currency = Currency(iso_code, full_name)
    Session.add(currency)
    try:
        Session.flush()
    except IntegrityError:
        raise ex.DuplicateCurrencyError()
    return currency