from celery.task import task
from jinja2.environment import Environment
from jinja2.loaders import PackageLoader
from tickee.accounts.manager import lookup_account_by_id
from tickee.users.manager import lookup_user_by_id
from tickee.users.tasks import mail_user
import logging
import transaction

#Session = sqlahelper.get_session()

env = Environment(loader=PackageLoader('tickee', 'templates'))
blogger = logging.getLogger("blm.account")

@task(name="routine.send_account_welcome_mail", 
      ignore_result=True)
def send_account_welcome_mail(user_id, account_id):
    """Sends an email to the account owner welcoming him to tickee and provides 
    him a link to activate his user account"""
    
    user = lookup_user_by_id(user_id)
    account = lookup_account_by_id(account_id)
      
    subject = "Your tickee account has been created"
    html_content = env.get_template('account_welcome.html').render(user=user, account=account)
    plain_content = env.get_template('account_welcome.txt').render(user=user, account=account)
    
    blogger.info('sending event notification mail to user %s' % user_id)
    success = mail_user(user_id, subject, html_content, plain_content)
#    success = random.choice([True, True, True, True, True, False])
    if not success:
        send_account_welcome_mail.retry(countdown=120)
    else:
        transaction.commit()