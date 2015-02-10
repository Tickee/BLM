'''
Created on 3 jan. 2012

@author: kevin
'''


def psp_to_dict(psp, short=False):
    result = dict(id=psp.id,
                  provider=psp.provider_type)
    if not short:
        result['data'] = dict(psp.provider_info)
    return result