from fabric.api import run, sudo, abort, local, settings, env, cd
import datetime

def staging():
    env.hosts = ['tickee-core']
    env.user = 'tickee'
    env.is_staging = True
    env.supervisor_worker = 'celery_staging'
    env.celery_settings = 'celeryconfig-staging.py'
    env.tickee_settings = 'settings-staging.py'
    env.code_dir = "/home/tickee/staging"
    
def production():
    env.hosts = ['tickee-core']
    env.user = 'tickee'
    env.is_staging = False
    env.supervisor_worker = 'celery_production'
    env.celery_settings = 'celeryconfig-production.py'
    env.tickee_settings = 'settings-production.py'
    env.code_dir = "/home/tickee/deploy"

def standby():
    env.hosts = ['tickee-one']
    env.user = 'tickee'
    env.is_staging = False
    env.supervisor_worker = 'celery_production'
    env.celery_settings = 'celeryconfig-production.py'
    env.tickee_settings = 'settings-production.py'
    env.code_dir = "/home/tickee/deploy"

# --- Mission Control ---    

def deploy():
    """Deploys new code to the selected server"""
    test()
    if not env.is_staging:
        backup()
    if env.is_staging:
        copy_db()
    prepare()
    worker_restart()

def status():
    """Shows the status of the workers"""
    worker_status()

def logs():
    """Follows the logs"""
    if env.is_staging:
        run('tail -n 100 -f ~/logs/tickee_blm.log')
    else:
        run('tail -n 100 -f ~/logs/tickee_blm.log')


# --- Backing up previous code ---

def backup():
    today = datetime.datetime.today().strftime('%d-%m-%Y_%H%M%S')
    with cd(env.code_dir):
        run('cp -r . ~/archive/%s' % today)

# --- Deploying new code ---

def prepare():
    """update to latest version"""
    with cd(env.code_dir):
        run('svn up core')
        run('svn up pyramid-oauth2')

def copy_db():
    """copy db from live to staging"""

# --- Supervisord ---

def worker_status():
    run("source ~/venvs/core/bin/activate && supervisorctl status")

def worker_stop():
    run("source ~/venvs/core/bin/activate && supervisorctl stop %s" % env.supervisor_worker, shell=False)

def worker_start():
    run("source ~/venvs/core/bin/activate && supervisorctl start %s" % env.supervisor_worker, shell=False)

def worker_restart():
    run("source ~/venvs/core/bin/activate && supervisorctl reread", shell=False)
    run("source ~/venvs/core/bin/activate && supervisorctl restart %s" % env.supervisor_worker, shell=False)

# --- Local ---

def test():
    """run test suite"""