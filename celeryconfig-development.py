from tickee.manage import reload_logging, load_database
from celerygeneric import *

# RabbitMQ::BLM
BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "blm"
BROKER_PASSWORD = "m0nkeP4w7"
BROKER_VHOST = "blmvhost"

#CELERY_SEND_TASK_ERROR_EMAILS = True

reload_logging(ini_file='./logging-development.ini')
load_database()