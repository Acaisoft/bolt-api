from keycloak import KeycloakAdmin, KeycloakOpenID


def k_admin(config):
    server_url = config.get('KEYCLOAK_URL')
    client_id = config.get('KEYCLOAK_CLIENT_ID')
    realm_name = config.get('KEYCLOAK_REALM_NAME')
    client_secret_key = config.get('KEYCLOAK_CLIENT_SECRET')

    return KeycloakAdmin(
        server_url=server_url,
        username='',
        password='',
        client_id=client_id,
        client_secret_key=client_secret_key,
        realm_name=realm_name,
        verify=True
    )


def k_client(config):
    server_url = config.get('KEYCLOAK_URL')
    client_id = config.get('KEYCLOAK_CLIENT_ID')
    realm_name = config.get('KEYCLOAK_REALM_NAME')
    client_secret_key = config.get('KEYCLOAK_CLIENT_SECRET')

    return KeycloakOpenID(
        server_url=server_url,
        client_id=client_id,
        realm_name=realm_name,
        client_secret_key=client_secret_key,
        verify=True
    )
