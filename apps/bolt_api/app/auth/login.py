import jwt

from datetime import datetime, timedelta

from flask import Blueprint, request, render_template, flash, redirect, current_app, make_response
from werkzeug.exceptions import Unauthorized, MethodNotAllowed

from services import const

bp = Blueprint('auth-login', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']

        if login != const.AUTH_LOGIN and \
                password != const.AUTH_PASSWORD:
            return Unauthorized('Invalid credentials')

        expires = datetime.utcnow() + timedelta(hours=const.JWT_VALID_PERIOD)
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

        priv_key = current_app.config.get(const.JWT_AUTH_PRIV_KEY, False)
        if not priv_key:
            return MethodNotAllowed('Service is not configured properly')

        token = jwt.encode(payload, priv_key, algorithm='RS256')

        response = make_response(redirect(const.REDIRECT_FRONT_URL))
        response.set_cookie('AUTH_TOKEN', token)
        return response

    return render_template('auth/login.html')
