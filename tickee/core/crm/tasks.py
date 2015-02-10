from tickee.core.crm.models import CrmDump
import sqlahelper

Session = sqlahelper.get_session()

def log_crm(object_name, object_id, data_dict):
    crmdata = CrmDump(object_name, object_id, data_dict)
    Session.add(crmdata)