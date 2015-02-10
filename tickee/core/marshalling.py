import calendar
import datetime
import logging

tlogger= logging.getLogger('technical')

# DATATYPES

def date(datetime_obj):
    if datetime_obj:
        return datetime_obj.strftime("%Y-%m-%dT%H:%M:%S")
    else:
        return None

def json_to_date(datetime_json):
    return datetime.datetime.strptime(datetime_json, "%Y-%m-%dT%H:%M:%S")


def timestamp(datetime_obj):
    if datetime_obj:
        return int(calendar.timegm(datetime_obj.timetuple()))
    else:
        return None


# ERRORS


def error(error):
    """ Default approach to generating error messages. """
    result = dict(error=error.error(),
                  error_number=error.error_number)
    return result



def internal_error(exception):
    """ Default approach to handling internal exceptions. """
    tlogger.exception(exception)
    return dict(error="An unknown error has occurred.")