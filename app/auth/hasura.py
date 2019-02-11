import logging

import jwt
from flask import make_response
from gql import gql

from app import const
from upstream.devclient import devclient


def hasura_token_for_user(config, user_email):
    email = user_email.lower()
    gql_client = devclient()
    allowed_roles = ['anonymous']
    role = ''

    resp = gql_client.execute(gql('''query ($eml: String!) {
        user(where:{email:{_eq:$eml}}) { 
            id email active is_admin is_manager is_reader 
        }
    }'''), variable_values={'eml': email})

    if resp.get('error', None):
        return resp

    user = resp.get('user', [])

    if not len(user):
        return make_response('user not registered', 400)

    user = user[0]

    if not user['active']:
        return make_response('user account not active', 400)

    if user["is_reader"]:
        allowed_roles.append(const.ROLE_READER)
        role = const.ROLE_READER

    if user["is_manager"]:
        allowed_roles.append(const.ROLE_MANAGER)
        role = const.ROLE_MANAGER

    if user["is_admin"]:
        allowed_roles.append(const.ROLE_ADMIN)
        role = const.ROLE_ADMIN

    payload = {"https://hasura.io/jwt/claims": {
        "x-hasura-allowed-roles": allowed_roles,
        "x-hasura-default-role": role,
        "x-hasura-user-id": user.get('id'),
        "x-hasura-user-email": email,
    }}

    logging.info('user authorized: %s', payload)

    algo = config.get(const.JWT_ALGORITHM, 'HS256')
    secret = config.get(const.SECRET_KEY)
    assert secret, 'SECRET_KEY not defined'
    return jwt.encode(payload, secret, algorithm=algo)
