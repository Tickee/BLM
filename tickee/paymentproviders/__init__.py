class TransactionInformation(object):
    buyer = None # UserInformation

class UserInformation(object):
    first_name = None
    last_name = None
    email = None


def elem2dict(node):
    """Convert an lxml.etree node tree into a dict."""
    d = {}
    for e in node.iterchildren():
        key = e.tag.split('}')[1] if '}' in e.tag else e.tag
        value = e.text if e.text else elem2dict(e)
        d[key] = value
    return d