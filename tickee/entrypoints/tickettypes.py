from celery.task import task
from tickee import logic
from tickee.entrypoints import marshalling
import transaction
import tickee.exceptions as ex


@task
def update_tickettype(oauth_client_id, tickettype_id, values_dict):
    """
    Entrypoint for updating tickettype information.
    
    Args:
        oauth_client_id:
            Id of the oauth client requesting the update
        tickettype_id:
            Id of the event to update
        values_dict:
            Dictionary containing information that requires updating. The 
            dictionary can contain the following information:
                -  active: Boolean for turning the event active or inactive.
    
    Returns:
        A dictionary containing a key "updated" which is True if the update
        was completed successfully and False if not. 
        
        {'updated': True}
        
        Even if nothing was updated, it will return True as a value to 
        indicate there were no problems encountered.
    """
    #TODO: Security - restrict updating by account owner
    em = logic.TicketManager()
    # check if activation is required
    try:
        tickettype = em.lookup_tickettype_by_id(tickettype_id)
        # handle "active"
        active = values_dict.get('active')
        if active:
            if unicode(values_dict.get('active')) == u'true':
                tickettype.publish()
            elif unicode(values_dict.get('active')) == u'false':
                tickettype.unpublish()
                
    except ex.TickeeError, e:
        transaction.abort()
        return marshalling.error(e)
    else:
        transaction.commit()
        return marshalling.updated_success_dict.copy()