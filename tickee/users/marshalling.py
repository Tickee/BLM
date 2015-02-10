def user_to_dict(user, include_name=True,
                       include_active=False):
    """
    Transforms a ``User`` object into a dictionary.
    """
    result = dict(id=user.id,
                  email=user.email)
    
    if 'social' in user.meta:
        result['social'] = user.meta.get('social')
    if 'address' in user.meta:
        result['address'] = user.meta.get('address')
    if 'crm' in user.meta:
        result['crm'] = user.meta.get('crm')
    if 'local' in user.meta:
        result['local'] = user.meta.get('local')
    if include_name:
        result['first_name'] = user.first_name or "None"
        result['last_name'] = user.last_name or "None"
    if include_active:
        result['active'] = user.is_active()
      
    return result