import os
import uuid

import jwt
from flask import current_app
from keycloak import KeycloakOpenID

from apps.bolt_api.app.utils.token import generate_token
from services import const
from services.logger import setup_custom_logger

logger = setup_custom_logger(__file__)


def hasura_token_for_testrunner(config):
    """
    Returns a token for use by a testrunner, granting access to a single execution.
    Token's generated either through Keycloak or locally depending on config
    :param config: flask app config
    :return: tuple: jwt token, testrunner id
    """

    if config.get(const.AUTH_KC, False):
        if config.get('SELFSIGNED_TOKEN_FOR_TESTRUNNER', False) or os.getenv('SELFSIGNED_TOKEN_FOR_TESTRUNNER', False):
            # provide token and execution id through environment, or one will be generated
            si_token = os.getenv('SELFSIGNED_TOKEN_EXECUTION_TOKEN', False)
            si_id = os.getenv('SELFSIGNED_TOKEN_EXECUTION_ID', False)
            if si_token and si_id:
                current_app.logger.info('using predefined testrunner token and execution id')
                return si_token, si_id
            current_app.logger.info('using selfsigned testrunner token')
            return hasura_selfsignedtoken_for_testrunner(config)

        server_url = config.get('KEYCLOAK_URL')
        client_id = config.get('KEYCLOAK_CLIENT_ID')
        realm_name = config.get('KEYCLOAK_REALM_NAME')
        client_secret_key = config.get('KEYCLOAK_CLIENT_SECRET')

        k_client = KeycloakOpenID(
            server_url=server_url,
            client_id=client_id,
            realm_name=realm_name,
            client_secret_key=client_secret_key,
            verify=True
        )

        token = k_client.token(grant_type='client_credentials')
        claims = jwt.decode(token['access_token'], options={"verify_signature": False})
        return token['access_token'], claims['https://hasura.io/jwt/claims']['x-hasura-testruner-id']
    else:
        logger.info("Generating Hasura access token inside service")
        execution_id = str(uuid.uuid4())
        payload = {
            "https://hasura.io/jwt/claims": {
                "x-hasura-allowed-roles": [const.ROLE_TESTRUNNER],
                "x-hasura-default-role": const.ROLE_TESTRUNNER,
                "x-hasura-testruner-id": execution_id,
            }}
        return generate_token(current_app.config, payload=payload), execution_id


#TODO: can be removed once AUTH_KC-driven approach above is tested
def hasura_selfsignedtoken_for_testrunner(config):
    """
    Returns a token for use by a testrunner, granting access to a single execution. Signed by config.SECRET_KEY, good for local tests.
    :param config: flask app config
    :param execution_id: resource ID to grant access to
    :return: str: jwt token
    """

    execution_id = os.getenv('SELFSIGNED_TOKEN_EXECUTION_ID', False)
    if not execution_id:
        execution_id = str(uuid.uuid4())

    payload = {"https://hasura.io/jwt/claims": {
        "x-hasura-allowed-roles": [const.ROLE_TESTRUNNER],
        "x-hasura-default-role": const.ROLE_TESTRUNNER,
        "x-hasura-testruner-id": execution_id,
    }}

    algo = config.get(const.JWT_ALGORITHM, 'HS256')
    secret = config.get(const.SECRET_KEY)
    assert secret, 'SECRET_KEY not defined'
    return jwt.encode(payload, secret, algorithm=algo), execution_id
