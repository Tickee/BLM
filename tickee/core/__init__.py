from tickee.core.exceptions import ApplicationError
from tickee.core.marshalling import error, internal_error
import transaction
from functools import wraps

def entrypoint(on_exception=None):
    
    def inner_entrypoint(f):
        
        def wrapper(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                transaction.commit()
                return result
            
            except ApplicationError as e:
                transaction.abort()
                # return application exception / user-specific value
                if on_exception is not None:
                    return on_exception
                else:
                    return error(e)
            
            except Exception as e:
                transaction.abort()
                return internal_error(e)
            
        return wraps(f)(wrapper)
    
    return inner_entrypoint