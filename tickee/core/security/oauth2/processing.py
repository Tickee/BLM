from pyramid_oauth2.models import OAuth2Client
import sqlahelper

Session = sqlahelper.get_session()

def create_oauth_client(account_name="Default Client for Account",
                        scopes=['scope_account_mgmt', 'scope_scanning', 
                                'scope_account_read', 'scope_order_mgmt']):
    client = OAuth2Client(account_name)
    Session.add(client)
    client.set_scopes(scopes)
    Session.flush()
    return client