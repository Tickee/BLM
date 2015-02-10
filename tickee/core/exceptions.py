class CoreError(Exception):
    """Base class for exceptions for Core."""
    
    def error(self):
        if self.message:
            return self.message
        else:
            return self.__doc__
        
class ApplicationError(Exception):
    """Base class for exceptions for the application."""
    
    def error(self):
        if self.message:
            return self.message
        else:
            return self.__doc__