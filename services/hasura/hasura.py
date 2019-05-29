import logging
import os
import uuid

import jwt
from flask import make_response, current_app
from gql import gql
from keycloak import KeycloakOpenID

from services import const
from services.hasura import hasura_client


def hasura_token_for_testrunner(config):
    """
    Returns a token for use by a testrunner, granting access to a single execution.
    Token's generated through
    :param config: flask app config
    :param execution_id: resource ID to grant access to
    :return: tuple: jwt token, testrunner id
    """

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
    claims = jwt.decode(token['access_token'], verify=False)
    return token['access_token'], claims['https://hasura.io/jwt/claims']['x-hasura-testruner-id']


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
