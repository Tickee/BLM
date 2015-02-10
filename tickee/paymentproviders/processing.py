from tickee.accounts.manager import lookup_account_by_id
from tickee.paymentproviders.manager import lookup_payment_provider_class_by_name
from tickee.paymentproviders.models import MonthlyTransactions
from tickee.paymentproviders.tasks import create_payment_provider
import datetime
import sqlahelper
import tickee.exceptions as ex

Session = sqlahelper.get_session()

def get_or_create_transaction_statistic(account, year=datetime.date.today().year,
                                          month=datetime.date.today().month):
    """Looks up the transaction statistic associated with an account."""
    stat = Session.query(MonthlyTransactions).filter_by(year=year,
                                                        month=month,
                                                        account_id=account.id).first()
    if stat is None:
        # create
        stat = MonthlyTransactions(account.id, year, month)
        Session.add(stat)
        Session.flush()
    return stat
                                                     

def increment_transaction_count(account, amount_of_tickets):
    """Increases the count of tickets associated with an account."""
    # lookup transaction statistics object
    stat = get_or_create_transaction_statistic(account)
    stat.amount += amount_of_tickets
    return stat


def create_payment_provider_information(account_id, psp_name, psp_data_dict):
    """Creates a paymentprovider for the account."""
    klass = lookup_payment_provider_class_by_name(psp_name)
    # fetch account belonging to the client
    account = lookup_account_by_id(account_id)

    if psp_data_dict is not None:
        # make sure all fields are available
        required_fields = klass.required_configuration_fields
        for field in required_fields:
            if not field in psp_data_dict:
                raise ex.PaymentError("following fields are required: %s" % ", ".join(required_fields))
    else:
        # ignore them
        psp_data_dict = {}
        
    # create payment provider
    provider_info = create_payment_provider(account, psp_data_dict, psp_name)
    return provider_info


def validate_payment_provider_information(provider_info, psp_data_dict):
    """validates the payment provider information making sure all mandatory fields are available."""
    # lookup psp class
    klass = lookup_payment_provider_class_by_name(provider_info.provider_type)
    # validate psp information
    required_fields = klass.required_configuration_fields
    for field in required_fields:
        if not field in psp_data_dict:
            raise ex.PaymentError("following fields are required: %s" % ", ".join(required_fields))