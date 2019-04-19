import json
import click
import jwt
from flask import current_app
from flask.cli import with_appcontext

from services.const import EXPORT_SCOPE_EXECUTION, EXPORT_SCOPE_PROJECT
from services.hasura.hasura import hasura_token_for_testrunner, hasura_selfsignedtoken_for_testrunner
from services.exports.data_export_token import issue_export_token


@click.command(name='job_token')
@click.argument('debug', required=False)
@with_appcontext
def job_token(debug=None):
    """
    Obtain and print access token for testrunner. KEYCLOAK_XXX has to be configured.

    [DEBUG] - by default token is issued by Keycloak, if true then a debug self-signed token will be used
    """
    if debug:
        token, execution_id = hasura_selfsignedtoken_for_testrunner(current_app.config)
    else:
        token, execution_id = hasura_token_for_testrunner(current_app.config)
    claims = jwt.decode(token, verify=False)
    print(f'> execution_id:\n{execution_id}')
    print(f'> access_token:\n{token}')
    print('> claims:')
    print(json.dumps(claims, indent=4))


@click.command(name='execution_data_export_token')
@click.argument('execution_id', required=True)
@click.argument('user_id', required=False)
@with_appcontext
def execution_data_export_token(execution_id, user_id=None):
    """
    Issue a token usable for data export to a Graphana instance. Use with Graphana's SimgpleJsonDatasource plugin.

    EXECUTION_ID - execution to grant access to

    [USER_ID] - user to grant access for
    """
    token = issue_export_token(current_app.config, EXPORT_SCOPE_EXECUTION, execution_id, user_id)
    print(f'> token:\n{token}')


@click.command(name='project_data_export_token')
@click.argument('project_id', required=True)
@click.argument('user_id', required=False)
@with_appcontext
def project_data_export_token(project_id, user_id=None):
    """
    Issue a token usable for data export to a Graphana instance. Use with Graphana's SimgpleJsonDatasource plugin.

    PROJECT_ID - execution to grant access to

    [USER_ID] - user to grant access for
    """
    token = issue_export_token(current_app.config, EXPORT_SCOPE_PROJECT, project_id, user_id)
    print(f'> token:\n{token}')
