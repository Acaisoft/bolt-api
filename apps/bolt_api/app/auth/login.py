import jwt

from datetime import datetime, timedelta

from flask import Blueprint, request, render_template, flash, redirect, current_app, make_response
from urllib.parse import urlparse

from services import const
from services.logger import setup_custom_logger

logger = setup_custom_logger(__file__)
bp = Blueprint('auth-login', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    redirect_url = request.args.get('redirect_url', False)
    priv_key = current_app.config.get(const.JWT_AUTH_PRIV_KEY, False)

    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']

        if login != current_app.config.get(const.AUTH_LOGIN) or \
                password != current_app.config.get(const.AUTH_PASSWORD):
            flash('Invalid credentials', 'error')
        else:
            expires = datetime.utcnow() + timedelta(hours=current_app.config.get(const.JWT_VALID_PERIOD))
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

            algorithm = current_app.config.get(const.JWT_ALGORITHM, 'RS256')

            token = jwt.encode(payload, priv_key, algorithm=algorithm)
            parsed_url = urlparse(redirect_url)
            app_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            base_url = urlparse(request.base_url)

            response = make_response(redirect(redirect_url))

            if current_app.config.get(const.AUTH_LOCAL_DEV, False):
                response.set_cookie('AUTH_TOKEN', token, samesite='None', secure=True)
                response.set_cookie('APP_URL', app_url, samesite='None', secure=True)
            else:
                response.set_cookie('AUTH_TOKEN', token, domain=base_url.netloc, samesite='None', secure=True)
                response.set_cookie('APP_URL', app_url, domain=base_url.netloc, samesite='None', secure=True)

            return response

    if not priv_key:
        flash('Service is not configured properly', 'error')

    if not redirect_url:
        flash('Expected "redirect_url" parameter in URL', 'error')

    return render_template('auth/login.html')
