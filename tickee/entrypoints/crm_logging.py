from celery.task import task
import tickee.logic as logic
import transaction

@task(ignore_result=True)
def log_request_information(json_bulk):
    """
    Logs the request information as a json dictionary. 
    
    ..note:: This is a temporary entrypoint.
    
    Args:
        json_bulk: json object containing the information to log.
    """
    lm = logic.LoggingManager()
    lm.log_request(json_bulk)
    transaction.commit()