# grants authorization to API_ACCOUNTS
from authlib.flask.oauth2 import AuthorizationServer


class DevServer(object):
    pass


authorization = AuthorizationServer(
    query_client=query_client,
    save_token=save_token,
)
