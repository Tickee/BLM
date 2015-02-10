from tickee.paymentproviders.manager import lookup_payment_provider
from tickee.paymentproviders.marshalling import psp_to_dict
def account_to_dict(account, include_theme=False, include_social=False, short=False):
    
    result = dict(id=account.id,
                  short_name=account.name,
                  name=account.full_name,
                  url=account.website,
                  email=account.email)
    
    if include_theme and 'theme' in account.meta:
        result['theme'] = account.meta.get('theme')
    if include_social and 'social' in account.meta:
        result['social'] = account.meta.get('social')
    if include_social and 'ext' in account.meta:
        result['ext'] = account.meta.get('ext')
    if "subtitle" in account.meta:
        result['subtitle'] = account.meta.get('subtitle')
    if not short:
        result['phone'] = account.meta.get('phone')
        result['vatnumber'] = account.meta.get('vatnumber')
        result['subscription'] = dict(type=account.subscription.subscription_type,
                                      url=account.subscription.meta.get('customer_url'))
    if not short:
        psp = lookup_payment_provider(account.id)
        if psp is not None:
            result['payment_provider'] = psp_to_dict(psp.payment_provider_info)
            
        result['currency'] = account.get_currency()
        result['handling_fee'] = account.get_handling_fee() / 100.0
        
    return result

def account_to_dict2(account, fields=["id", "name", "short_name"]):
    result = dict()
    for field in fields:
        if field == "id":
            result['id'] = account.id
        elif field == "name":
            result['name'] = account.full_name
        elif field == "short_name":
            result['short_name'] = account.name
        elif field == "subtitle":
            result['subtitle'] = account.meta.get('subtitle')
        elif field == "social":
            result['social'] = account.meta.get('social')
        elif field == "ext":
            result['ext'] = account.meta.get('social')
        elif field == "theme":
            result['theme'] = account.meta.get('theme')
        elif field == "url":
            result['url'] = account.website
        elif field == "email":
            result['email'] = account.email
    return result