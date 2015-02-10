from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.types import TypeDecorator, Text, MutableType
import collections
import copy
import simplejson

class JSONEncodedDict(TypeDecorator):
    "Represents an immutable structure as a json-encoded string."

    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            return simplejson.dumps(value, use_decimal=True)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return simplejson.loads(value, use_decimal=True)
        return value



class MutationDict(Mutable, dict):
    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutationDict."

        if not isinstance(value, MutationDict):
            if isinstance(value, dict):
                return MutationDict(value)

            # this call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        "Detect dictionary set events and emit change events."

        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        "Detect dictionary del events and emit change events."

        dict.__delitem__(self, key)
        self.changed()
        
        
        
class JSONEncodedList(MutableType, JSONEncodedDict):
    """Adds mutability to list type JSONEncodedDict. Use scarsely"""

    def copy_value(self, value):
        if value    : return value[:]
        else        : return []