from typing import Optional

import jwt
from datetime import datetime, timedelta
from flask import Config

from services import const


def generate_token(config: Config, priv_key: Optional[str] = None, payload: Optional[dict] = None) -> str:
    """
    Generates token that is digestible by Hasura.
    Just a boilerplate containing hardcoded, critical payload needed to authenticate user
    :param config: flask app config
    :param priv_key: (optional) private key to sign token with. Will be taken from config if not passed explicitly.
    :param payload: (optional) payload to encode in token. Defaults to critical set of variables needed to authenticate
    with Hasura
    :return: str: jwt token
    """
    if priv_key is None:
        priv_key = config.get(const.JWT_AUTH_PRIV_KEY, False)
        if not priv_key:
            raise Exception(f'{const.JWT_AUTH_PRIV_KEY} is missing in config')
    expires = datetime.utcnow() + timedelta(hours=config.get(const.JWT_VALID_PERIOD))
    if payload is None:
        payload = {
            "exp": expires,
            "allowed-origins": [
                "*"
            ],
            "realm_access": {
                "roles": [
                    "offline_access",
                    "uma_authorization"
                ]
            },
            "resource_access": {
                "bolt-portal": {
                    "roles": [
                        "manager",
                        "reader",
                        "tester",
                        "tenantadmin"
                    ]
                },
                "account": {
                    "roles": [
                        "manage-account",
                        "manage-account-links",
                        "view-profile"
                    ]
                }
            },
            "scope": "openid profile email",
            "email_verified": True,
            "https://hasura.io/jwt/claims": {
                "x-hasura-default-role": "tenantadmin",
                "x-hasura-allowed-roles": [
                    "tenantadmin",
                    "manager",
                    "tester",
                    "reader"
                ],
                "x-hasura-user-id": "96fa4735-f862-4cb9-b0df-f09c008e02e4"
            },
            "name": "Bolt Dev",
            "preferred_username": "bolt+dev@acaisoft.com",
            "given_name": "Bolt",
            "family_name": "Dev",
            "email": "bolt+dev@acaisoft.com"
        }

    algorithm = config.get(const.JWT_ALGORITHM, 'RS256')

    return jwt.encode(payload, priv_key, algorithm=algorithm)
