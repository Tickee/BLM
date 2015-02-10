from tickee.accounts.manager import lookup_account_by_id
from tickee.db.models.event import Event
from tickee.events.eventparts.processing import delete_eventpart
from tickee.tickettypes.processing import delete_tickettype
import datetime
import logging
import sqlahelper

blogger = logging.getLogger('blm.events')

Session = sqlahelper.get_session()

def delete_event(event):
    """ Removes the event """
    # remove tickettypes
    for tickettype in event.get_ticket_types(True, True):
        delete_tickettype(tickettype)
    # remove eventparts
    for eventpart in event.parts:
        delete_eventpart(eventpart)
    # remove event
    blogger.debug('delete event %s' % event.id)
    Session.delete(event)


def start_event(account_id, name, 
                start_datetime=datetime.datetime.today(), 
                end_datetime=datetime.datetime.today()+datetime.timedelta(hours=24)):
    """
    Creates a new event.
    
    Args:
        account_id:
            The id of the ``Account`` organizing the ``Event``.
        name:
            The name of the event, e.g. "Lokerse Feesten 2011"
        start_datetime (optional):
            The date and time when the event starts. Defaults to today.
        end_datetime (optional):
            The date and time when the event ends. Defaults to tomorrow.
            
    Returns:
        The ``Event`` that was created
        
    Raises:
        AccountNotFoundError:
            No account with the account_id was found.
    """
    # validate account exists
    lookup_account_by_id(account_id)
    # create event
    event = Event(name, None, account_id)
    Session.add(event)
    Session.flush()
    return event