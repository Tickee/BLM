import datetime

BROKER_POOL_LIMIT = 10

ADMINS = [
    ('Koen Betsens', 'koen@tick.ee')
]

CELERY_AMQP_TASK_RESULT_EXPIRES = 60
#CELERY_TASK_RESULT_EXPIRES = None
CELERY_RESULT_BACKEND = "amqp"
CELERY_IMPORTS = (
    'tickee.users.tasks',
    'tickee.orders.tasks',
    'tickee.tickets.tasks',
    'tickee.events.tasks',
    'tickee.tickets.entrypoints',
    'tickee.tickettypes.entrypoints',
    'tickee.statistics.entrypoints',
    'tickee.accounts.entrypoints',
    'tickee.events.entrypoints',
    'tickee.events.eventparts.entrypoints',
    'tickee.orders.entrypoints',
    'tickee.scanning.entrypoints',
    'tickee.venues.entrypoints',
    'tickee.paymentproviders.entrypoints',
    'tickee.users.entrypoints',
    'tickee.subscriptions.entrypoints',
    'pyramid_oauth2.oauth2.authorization'
)

CELERYBEAT_SCHEDULE = {
    "session-timeout": {
        "task": "tickee.orders.tasks.timeout_sessions",
        "schedule": datetime.timedelta(seconds=30)
    },
    "event-in-48-hours-notification": {
        "task": "routine.event_in_48_hours_reminder",
        "schedule": datetime.timedelta(hours=1)
    }
}

#SERVER_EMAIL = "droid@tick.ee"
#EMAIL_HOST = 'smtp.gmail.com'
#EMAIL_HOST_USER = "tickets@tick.ee"
#EMAIL_HOST_PASSWORD = "fd-55_ty44"
#EMAIL_PORT = 587
#EMAIL_USE_SSL = True
#EMAIL_TIMOUT = 3 * 60