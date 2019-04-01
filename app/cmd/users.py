import json
import click
from flask import current_app
from flask.cli import with_appcontext
from gql import gql
from schematics import types

from app import const
from app.hasura_client import hasura_client
from app.keycloak.clients import kclient


@click.command(name='user_create')
@click.argument('email', required=True)
@click.argument('project', required=True)
@click.argument('role', required=True)
@with_appcontext
def user_create(email, project, role):
    """
    Create a user in keycloak with given roles
    """
    e = types.EmailType(max_length=256)
    e.validate(email)
    p = types.UUIDType()
    p.validate(project)
    r = types.BaseType(choices=const.ROLE_CHOICE)
    r.validate(role)

    gqlclient = hasura_client(current_app.config)
    gqlclient.execute(gql('''query {
        project_by_pk(
    }'''), )

    client = kclient(current_app.config)
    print(client)
