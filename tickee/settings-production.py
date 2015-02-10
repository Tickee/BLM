from sqlalchemy.pool import NullPool

DATABASE = {
    'url': 'postgresql://tickee:onlyone_nivek@localhost:5432/tickee_prod',
    'poolclass': NullPool
}

# All packages containing a models package necessary for creating the database
INSTALLED_APPS = (
    'tickee.db',
    'tickee.paymentproviders',
    'tickee.core.currency',
    'tickee.core.crm',
    'tickee.core.l10n',
#    'tickee.accounts',
#    'tickee.events',
#    'tickee.orders',
    'tickee.scanning',
    'tickee.subscriptions',
    'tickee.tickets',
#    'tickee.tickettypes',
#    'tickee.users',
    'tickee.venues',
)

SMTP_SERVERS = [
    {
        'name': 'Sendgrid',
        'host': 'smtp.sendgrid.net',
        'port': 587,
        'tls': True,
        'username': 'tickee',
        'password': 'onlyone_tickee'
    },
    {
        'name': 'Gmail',
        'host': 'smtp.gmail.com',
        'port': 587,
        'tls': True,
        'username': 'noreply@tick.ee',
        'password': '1.kwarteL'
    }
]