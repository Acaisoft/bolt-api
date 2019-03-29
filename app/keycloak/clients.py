from keycloak import KeycloakAdmin


def kclient(config):
    server_url = config.get('KEYCLOAK_URL')
    client_id = config.get('KEYCLOAK_CLIENT_ID')
    realm_name = config.get('KEYCLOAK_REALM_NAME')
    client_secret_key = config.get('KEYCLOAK_CLIENT_SECRET')

    c = KeycloakAdmin(
        server_url=server_url,
        username='',
        password='',
        client_id=client_id,
        client_secret_key=client_secret_key,
        realm_name=realm_name,
        verify=True
    )
    return c
