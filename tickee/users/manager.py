from tickee.db.models.user import User
import sqlahelper
import tickee.exceptions as ex

Session = sqlahelper.get_session()


def lookup_user_by_id(user_id):
    """
    Retrieves the user with the given id.
    
    Args:
        user_id:
            The id of the user to return
            
    Returns:
        ``User`` object connected to the user_id
        
    Raises:
        UserNotFoundError 
            No user was found matching the user_id.
    """
    user = Session.query(User).get(user_id)
    if not user:
        raise ex.UserNotFoundError()
    return user


def lookup_user_by_email(email):
    """
    Retrieves the user with the given email.
    
    Args:
        email:
            The email of the user to return
            
    Returns:
        ``User`` object connected to the email
        
    Raises:
        UserNotFoundError 
            No user was found matching the email.
    """
    user = Session.query(User).filter(User.email == email).first()
    if not user:
        raise ex.UserNotFoundError()
    return user


def lookup_user_by_activation_code(activation_code):
    """
    Retrieves the user with an particular activation code.
    
    Args:
        activation_code:
            The activation code of the user
            
    Returns:
        ``User`` object that was activated
    
    Raises:
        UserNotFoundError
            No user was found matching the activation_code
    """
    user = Session.query(User).filter(User.activation_key==activation_code).first()
    if not user:
        raise ex.UserNotFoundError()
    return user