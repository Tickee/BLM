import re
from tickee.core.exceptions import CoreError

class ValidationError(CoreError):
    """Errors concerning validation of information"""


email_re = re.compile(
               "[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?",
                re.IGNORECASE)

def validate_email(value):
    if value is None:
        raise ValidationError("email validator received None")
    if not email_re.search(value):
        raise ValidationError("the email address '%s' was not valid" % value)

