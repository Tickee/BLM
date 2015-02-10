def client_to_dict(client, include_credentials=False, include_scopes=True):
    """
    Transforms a ``OAuth2Client`` object into a dictionary.
    """
    result = dict(id=client.id,
                  name=client.name)
    if include_scopes:
        result['scope'] = client.allowed_scopes
    if include_credentials:
        result['key'] = client.key
        result['secret'] = client.secret
    return result