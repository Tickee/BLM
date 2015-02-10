from sqlalchemy.exc import IntegrityError
from tickee.db.models.user import User
import logging
import sqlahelper
import tickee.exceptions as ex

Session = sqlahelper.get_session()

tlogger = logging.getLogger('technical')
blogger = logging.getLogger('blm.users')

def create_user(email):
    """
    Creates an inactive user
    
    Args:
        email
            email which will be used for communication.
    
    Returns:
        The newly created ``User`` object.
        
    Raises:
        UserError:
            A user with that email already exists.
    """
    user = User(email)
    Session.add(user)
    try:
        Session.flush()
    except IntegrityError as e:
        raise ex.UserError("A user with that email already exists.")
    blogger.info("user %s created: %s" % (user.id, email))
    # deactivate user for tickee
    user.reset()
    # send activation mail
#        send_activation_mail.delay(user.id)  
    return user