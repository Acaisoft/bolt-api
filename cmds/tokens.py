import json
import os

import click
import jwt
from flask import current_app
from flask.cli import with_appcontext

from services.hasura.hasura import hasura_token_for_testrunner, hasura_selfsignedtoken_for_testrunner


@click.command(name='job_token')
@click.option('--debug', default=False, is_flag=True)
@with_appcontext
def job_token(debug=False):
    """
    Obtain and print access token for testrunner. KEYCLOAK_XXX has to be configured.

    [DEBUG] - by default token is issued by Keycloak, if true then a debug self-signed token will be used
    """
    if debug:
        token, execution_id = hasura_selfsignedtoken_for_testrunner(current_app.config)
    else:
        token, execution_id = hasura_token_for_testrunner(current_app.config)
    claims = jwt.decode(token, options={"verify_signature": False})
    print(f'> execution_id:\n{execution_id}')
    print(f'> access_token:\n{token}')
    print('> claims:')
    print(json.dumps(claims, indent=4))
