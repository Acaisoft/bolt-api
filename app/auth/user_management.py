from flask import current_app
from gql import gql
from schematics import types

from app import const
from app.hasura_client import hasura_client
from app.keycloak.users import create_user_with_role


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

    current_app.logger.info('adding keycloak user')
    user_id = create_user_with_role(current_app.config, email, role)
    assert user_id, f'expected a non-empty keycloak user_id instead of {user_id}'

    current_app.logger.info('adding user-project relation')
    gqlclient.execute(gql('''mutation ($data:user_project_insert_input!) {
        insert_user_project(objects: [$data]) { affected_rows }
    }'''), {'data': {'user_id': user_id, 'project_id': project}})

    return user_id
