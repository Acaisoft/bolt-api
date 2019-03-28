import json
import click
import jwt
from flask import current_app
from flask.cli import with_appcontext
from app.auth.hasura import hasura_token_for_testrunner


@click.command(name='job_token')
@with_appcontext
def job_token():
    """
    Obtain and print access token for testrunner. KEYCLOAK_XXX has to be configured.
    :return:
    """
    token, execution_id = hasura_token_for_testrunner(current_app.config)
    claims = jwt.decode(token, verify=False)
    print(f'> execution_id:\n{execution_id}')
    print(f'> access_token:\n{token}')
    print('> claims:')
    print(json.dumps(claims, indent=4))
