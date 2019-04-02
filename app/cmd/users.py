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
    project_query = gqlclient.execute(gql('''query ($project:uuid!) {
        project_by_pk (id:$project) {
            is_deleted
            name
            userProjects { user_id }
        }
    }'''), {'project': project})
    assert project_query['project_by_pk'], f'invalid project id f{project}: {project_query}'

    client = kclient(current_app.config)
    print(client)

    import ipdb; ipdb.set_trace()
    needs_registration = True
    users = client.get_users({})
    print(users)
    for u in users:
        if u['email'] == email:
            needs_registration = False

    if needs_registration:
        new_user = client.create_user({
            "email": email,
            "username": email,
            "enabled": True,
        })
        print(new_user)

        # force user to register and setup password
        response = client.send_verify_email(user_id=new_user['id'])
        # TODO: setup user password
        print(response)

    # assign bolt client role to user
    bolt_client_id = client.get_client_id('Bolt')
    role_id = client.get_client_role_id(client_id=bolt_client_id, role_name=role)
    client.assign_client_role(client_id=bolt_client_id, user_id=new_user['id'], role_id=role_id, role_name=role)
