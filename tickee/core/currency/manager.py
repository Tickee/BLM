from tickee.core.currency.models import Currency
import sqlahelper
import tickee.exceptions as ex


Session = sqlahelper.get_session()

def lookup_currency_by_iso_code(iso_code):
    """
    Finds the currency belonging to the ISO code.
    
    Args:
        iso_code:
            The ISO 4217 code of the currency
    
    Returns:
        The found ``Currency`` object.
        
    Raises:
        CurrencyNotFoundError:
            The currency with that ISO code is not found.
    """
    currency = Session.query(Currency).filter(Currency.name==iso_code).first()
    if not currency:
        raise ex.CurrencyNotFoundError()
    return currency