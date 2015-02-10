from celery.task import task
from tickee.db.models.tickettype import TicketTypeEventPartAssociation
from tickee.tickettypes.manager import lookup_tickettype_by_id
import logging
import sqlahelper
import tickee.exceptions as ex
import transaction

Session = sqlahelper.get_session()

blogger = logging.getLogger('blm.tickettypes')

# Asynchronous Tasks

@task
def update_availability(tickettype_id):
    """Checks if the availability of the tickettype needs to be changed."""
    try:
        tickettype = lookup_tickettype_by_id(tickettype_id)
    except ex.TicketTypeNotFoundError:
        blogger.error("failed updating availability: tickettype %s not found" % tickettype_id)
        transaction.abort()
    else:
        tickettype.update_availability()
        transaction.commit()

# Synchronous Tasks




    

    