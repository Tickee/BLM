from celery.task import task
from tickee.core.validators import validate_email, ValidationError
import logging
import marshalling
import tickee.exceptions as ex
import tickee.logic as logic
import tickee.orders.manager as om
import transaction

blogger = logging.getLogger("blm.user")

@task
def user_info(client_id, email):
    """
    Returns information about the user and his orders.
    """
    um = logic.UserManager()
    try:
        user = um.lookup_user_by_email(email)
        orders = om.get_orders_of_user(user.id)
    except ex.TickeeError as e:
        transaction.abort()
        return marshalling.error(e)
    except Exception as e:
        transaction.abort()
        return marshalling.internal_error(e)
    else:
        result = dict(first_name=user.first_name,
                      last_name=user.last_name,
                      email=user.email,
                      orders=map(lambda o: dict(id=o.id,
                                                tickets=map(lambda t: marshalling.ticket_to_dict(t, include_scanned=True,
                                                                                                 include_user=False), 
                                                            o.get_tickets()),
                                                status=o.status,
                                                date=marshalling.date(o.session_start)), 
                                 orders))
        return result

@task
def create_user(email, password):
    """
    Entrypoint for creating new users.
    
    Args:
        email:
            Personal email address of the user
        password:
            Password of the user.
            
    Returns:
        A dictionary containing the information of the newly created user
        including his identifier. A ``created`` key-value pair is added 
        indicating the success of the attempt. For example:
        
        {'created': True,
         'user': {"id": 42, 
                  "email": "info@example.com"}}
         
        The dictionary will only contain the created key if the attempt was not
        successful:
        
        {'created': False}
    """
    um = logic.UserManager()
    try:
        # validate if email contains actually a valid email address:
        validate_email(email)
        # create account
        user = um.create_user(email)
        if password:
            user.set_password(password)
        else:
            user.reset()
    except ex.TickeeError as e:
        transaction.abort()
        # build failed result
        return marshalling.error(e)
    except ValidationError as e:
        transaction.abort()
        return marshalling.error(e)
    else:
        user_info = marshalling.user_to_dict(user)
        transaction.commit()
        # build success result
        result = marshalling.created_success_dict.copy()
        result['user'] = user_info
        return result


@task
def user_exists(email):
    """
    Entrypoint for checking if a user with a given email already exists.
    
    Args:
        email:
            The email address that needs to be checked for existence.
            
    Returns:
        A dictionary {'exists': True} if it exists. If there is no user found
        with the email address, the value will be False.
    """
    um = logic.UserManager()
    try:
        user = um.lookup_user_by_email(email)
    except ex.TickeeError, e:
        transaction.abort()
        return dict(exists=False)
    else:
        transaction.commit()
        return dict(exists=True,
                    id=user.id)
        
        
@task
def activate_user(activation_code, new_password):
    """
    Entrypoint for activating a user. Also sets their password if 
    
    Args:
        activation_code:
            The activation code used to activate a user.
            
        new_password:
            The password that has to be set for the user
    
    Returns:
        A dictionary {'activated': True} if the user was successfully 
        activated. If no user was found matching the activation code, 
        the value will be False.
    """
    um = logic.UserManager()
    try:
        user = um.lookup_user_by_activation_code(activation_code)
        user.activate()
        user.set_password(new_password)
    except ex.UserNotFoundError:
        blogger.debug("no user found with activation code %s" % activation_code)
        transaction.abort()
        return dict(activated=False)
    else:
        transaction.commit()
        return dict(activated=True)
    
    