from celery.task import task
from tickee.accounts.manager import lookup_accounts_of_user
from tickee.accounts.marshalling import account_to_dict2
from tickee.core import entrypoint
from tickee.core.validators import validate_email, ValidationError
from tickee.users.manager import lookup_user_by_id, lookup_user_by_email
from tickee.users.marshalling import user_to_dict
from tickee.users.processing import create_user
from tickee.users.tasks import send_activation_mail, send_recovery_mail
import datetime
import logging
import tickee.exceptions as ex

tlogger = logging.getLogger('technical')

@task(name="users.deactivate")
@entrypoint()
def user_deactivate(user_id):
    """ deactivates the user """
    user = lookup_user_by_id(user_id)
    user.deactivate()
    return user_to_dict(user)


@task(name="users.validate_password")
@entrypoint()
def validate_password(user_id, password):
    """ Entrypoint for verifying if there exists a user 
    matching email & password """
    user = lookup_user_by_id(user_id)
    # valid password
    if user.check_password(password):
        user.last_login = datetime.datetime.utcnow()
        result = dict(user=user_to_dict(user),
                      accounts=map(lambda a: account_to_dict2(a,
                                                              fields=["short_name", "name"]),
                                   lookup_accounts_of_user(user)))
        return result
        
    # invalid password
    else:
        raise ex.UserNotFoundError()


@task(name="users.recover_password")
@entrypoint()
def recover_password(user_id):
    """ Generates a recovery key and mails it to the user """
    user = lookup_user_by_id(user_id)
    user.create_recovery_code()
    send_recovery_mail(user.id)
    


@task(name="users.update")
@entrypoint()
def user_update(user_id, user_info):
    """ Replaces a user's data with the information located in user_info """
    user = lookup_user_by_id(user_id)
    for (key, value) in user_info.iteritems():
        if key == "first_name" and value is not None:
            user.first_name = value
        elif key == "last_name" and value is not None:
            user.last_name = value
        elif key == "email" and value is not None:
            try:
                lookup_user_by_email(value)
            except:
                user.email = value
        elif key == "password" and value is not None:
            user.set_password(value)
        elif key == "active" and value is not None:
            if value:
                user.activate()
            else:
                user.deactivate()
                send_activation_mail.delay(user_id)
        elif key == "social" and value is not None:
            user.meta['social'] = value
        elif key == "address" and value is not None:
            user.meta['address'] = value
        elif key == "crm" and value is not None:
            user.meta['crm'] = value
        elif key == "local" and value is not None:
            user.meta['local'] = value
    return user_to_dict(user)


@task
@entrypoint()
def user_create(client_id, email, password=None, first_name=None, last_name=None, user_info=None):
    """
    Entrypoint for creating new users.
    
    Args:
        email:
            Personal email address of the user
        password:
            Password of the user.
            
    Returns:
        {
            "id": 480
            "first_name": null,
            "last_name": null,
        }
    """
    # validate if email contains actually a valid email address:
    try:
        validate_email(email)
    except ValidationError:
        raise ex.UserError("please enter a valid email address")
    # create account
    user = create_user(email)
    user.first_name = first_name
    user.last_name = last_name
    if password:
        user.set_password(password)
    if user_info:
        for (key, value) in user_info.iteritems():
            if key == "social" and value is not None: user.meta['social'] = value
            elif key == "address" and value is not None: user.meta['address'] = value
            elif key == "crm" and value is not None: user.meta['crm'] = value
            elif key == "local" and value is not None: user.meta['local'] = value
    
    user_info = user_to_dict(user, include_name=True)

    # build success result
    return user_info
    
    
@task
@entrypoint()
def user_details(user_id, activation_token):
    """ Returns information about the user. If an activation token is added, 
    it will return a NoUserFound exception if the token does not match. """
    user = lookup_user_by_id(user_id)

    if activation_token is not None:
        if user.activation_key == activation_token or\
           user.is_valid_recovery_code(activation_token):
            return user_to_dict(user, include_name=True)
        else:
            raise ex.UserNotFoundError()

    return user_to_dict(user, include_name=True, include_active=True)
    
    
@task
@entrypoint(on_exception=False)
def user_exists(email):
    """
    Entrypoint for checking if a user with a given email already exists.
    
    Args:
        email:
            The email address that needs to be checked for existence.
        activation_token:
            
            
    Returns:
        A dictionary {'exists': True} if it exists. If there is no user found
        with the email address, the value will be False.
    """
    user = lookup_user_by_email(email)
    return user_to_dict(user, include_name=True, include_active=True)