'''
Created on 10-aug-2011

@author: kevin
'''
from tickee.core.exceptions import ApplicationError

class TickeeError(ApplicationError):
    """Base class for exceptions for Tickee."""
    error_number = 0
    
    def error(self):
        if self.message:
            return self.message
        else:
            return self.__doc__

# ------------------------------------------------------------------------------

class SubscriptionError(TickeeError):
    """Exceptions related to subscriptions"""
    error_number = 100

# ------------------------------------------------------------------------------

class PaymentError(TickeeError):
    """Exceptions related to payment providers"""
    error_number = 200

# ------------------------------------------------------------------------------

class VenueError(TickeeError):
    """Exceptions related to a location"""
    error_number = 300
    
    
class VenueNotFoundError(VenueError):
    """Venue was not found"""

class AddressNotFoundError(VenueError):
    """Address was not found"""

class VenueExistsError(VenueError):
    """Venue already exists"""

# ------------------------------------------------------------------------------

class OrderError(TickeeError):
    """Exceptions related to an order"""
    error_number = 400


class InvalidOrderError(OrderError):
    """Exceptions regarding invalid order amounts"""

class EmptyOrderError(OrderError):
    """Action can not be completed because the order is empty."""

class AmountNotAvailableError(OrderError):
    """Exceptions related to ordering too many tickets"""

class OrderNotFoundError(OrderError):
    """Exceptions for unexisting order"""

class AlreadyPurchasedOrderError(OrderError):
    """Exceptions for orders that are already purchased"""

class OrderLockedError(OrderError):
    """Action can not be completed because the order is locked."""

class NoAttachedPaymentProviderError(OrderError):
    """There is no payment service provider connected to the order."""

# ------------------------------------------------------------------------------

class AccountError(TickeeError):
    """Exception related to accounts"""
    error_number = 500


class AccountNotFoundError(AccountError):
    """No account found"""

# ------------------------------------------------------------------------------

class UserError(TickeeError):
    """Exceptions related to a user"""
    error_number = 600


class UserNotFoundError(UserError):
    """Exceptions related to no user found"""

class UserAssociationError(UserError):
    """Exception related to associating an account to a user"""

# ------------------------------------------------------------------------------

class TicketError(TickeeError):
    """Exceptions related to a tickets"""
    error_number = 700

class DuplicateTicketScanError(TicketError):
    """The ticket has already been scanned in."""
    error_number = 701

class TicketNotFoundError(TicketError):
    """The ticket was not found."""
    error_number = 702

class TicketTypeNotFoundError(TicketError):
    """Exception related to not found ticket types"""
    
class InactiveTicketTypeError(TicketError):
    """Ticket Type is not available"""

class InvalidPriceError(TicketError):
    """Ticket Type has an invalid price"""

class InvalidAmountError(TicketError):
    """Ticket Type has an invalid amount of units"""


    


# ------------------------------------------------------------------------------

class EventError(TickeeError):
    """Exceptions related to events"""
    error_number = 800

    
class EventNotFoundError(EventError):
    """No event found"""
    
class EventPartNotFoundError(EventError):
    """No event part found"""

# ------------------------------------------------------------------------------
    
class CurrencyError(TickeeError):
    """Excceptions related to currency"""
    error_number = 900


class CurrencyNotFoundError(CurrencyError):
    """No currency found."""

class DuplicateCurrencyError(CurrencyError):
    """The currency already exists in the database"""
    
# ------------------------------------------------------------------------------

class PermissionDenied(TickeeError):
    """You are not allowed to execute this task"""
    error_number = 1000

# ------------------------------------------------------------------------------