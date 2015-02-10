from celery.task import task
from jinja2.environment import Environment
from jinja2.loaders import PackageLoader
from tickee.core.mail import send_email
from tickee.db.models.user import User
from tickee.users.manager import lookup_user_by_id
import datetime
import logging
import sqlahelper

Session = sqlahelper.get_session()

env = Environment(loader=PackageLoader('tickee', 'templates'))

blogger = logging.getLogger("blm.user")

@task
def mail_user(user_id, subject, html_content, plain_content="", fake=False):
    """ Sends the user a templated mail with a specific content. """
    try:
        user = lookup_user_by_id(user_id)
        html_template = env.get_template('base.html').render(user=user,
                                                             content=html_content)
        plain_template = env.get_template('base.txt').render(user=user,
                                                             plain_content=plain_content)
        
        if user.email is None:
            raise Exception('user has no email address')
        
        blogger.info('sending mail to user %s (%s)' % (user.id, user.email))
        
        sender = "Tickee <noreply@tick.ee>"
        
        if not fake:
            send_email(sender, user.email, subject, html_template, plain_template, noreply=True)
            
    except:
        blogger.exception('failed sending user mail to user %s' % user_id)
        return False
    else:
        return True

@task
def send_recovery_mail(user_id, fake=False):
    """
    Sends the user his recovery code.
    
    Arguments:
        user_id: 
            unique id of the user that needs to receive activation information.
        fake:
            boolean to fake email sending (for testing purposes)
    """
    # fetch database information
    user = Session.query(User).get(user_id)
    
    # do not send if no activation code exists
    if not user.has_recovery_window():
        blogger.error("failed sending mail: user %s has no recovery window." % user_id)
        return
    
    # Create template
    html_content = env.get_template('recovery_mail.html').render(user=user,
                                                                 date=datetime.datetime.utcnow())
    plain_content = env.get_template('recovery_mail.txt').render(user=user,
                                                                 date=datetime.datetime.utcnow())
    
    mail_user(user_id, "Recover your tickee password", html_content, plain_content, fake)




@task
def send_activation_mail(user_id, fake=False):
    """
    Sends the user his activation code.
    
    Arguments:
        user_id: 
            unique id of the user that needs to receive activation information.
        fake:
            boolean to fake email sending (for testing purposes)
    """
    # fetch database information
    user = Session.query(User).get(user_id)
    
    # do not send if no activation code exists
    if not user.activation_key:
        blogger.error("user %s does not have an activation code" % user_id)
        return
    
    # Create template
    html_content = env.get_template('activation_mail.html').render(user=user,
                                                                   date=datetime.datetime.utcnow())
    plain_content = env.get_template('activation_mail.txt').render(user=user,
                                                                   date=datetime.datetime.utcnow())
    
    mail_user(user_id, "Activate your tickee account", html_content, plain_content, fake)