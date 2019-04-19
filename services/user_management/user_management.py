from flask import current_app
from schematics import types

from services import const
from services.hasura import hce
from services.keycloak.users import create_user_with_role, list_users, user_assign_roles


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

    project_query = hce(current_app.config, '''query ($project:uuid!) {
        project_by_pk (id:$project) {
            is_deleted
            name
            userProjects { user_id }
        }
    }''', {'project': project})
    assert project_query['project_by_pk'], f'invalid project id f{project}: {project_query}'

    current_app.logger.info('adding keycloak user')
    user_id = create_user_with_role(current_app.config, email, role)
    assert user_id, f'expected a non-empty keycloak user_id instead of {user_id}'

    current_app.logger.info('adding user-project relation')
    hce(current_app.config, '''mutation ($data:user_project_insert_input!) {
        insert_user_project(objects: [$data]) { affected_rows }
    }''', {'data': {'user_id': user_id, 'project_id': project}})

    return user_id


def user_unassign_from_project(user_id, project_id):
    p = types.UUIDType()
    p.validate(user_id)
    p.validate(project_id)

    return hce(current_app.config, '''mutation ($user_id:UUID!, $project_id:UUID!) {
        delete_user_project(where:{
            user_id:{_eq:$user_id}
            project_id:{_eq:$project_id}
        }) { returning { user_id project_id } }
    }''', {
        'user_id': user_id,
        'project_id': project_id,
    })


def list_users_in_project(project_id):
    p = types.UUIDType()
    p.validate(project_id)

    response = hce(current_app.config, '''query ($project:uuid!) {
        user_project (where:{project_id:{_eq:$project}}) { user_id }
    }''', {'project': project_id})
    assert response['user_project'], f'invalid project id f{project_id}: {response}'

    user_ids = set([x['user_id'] for x in response['user_project']])

    current_app.logger.info(f'looking up {len(user_ids)} users: {user_ids}')
    k_users = list_users(current_app.config)

    return [x for x in k_users if x.get('id', None) in user_ids]


def user_roles_update(user_id, new_roles):
    p = types.UUIDType()
    p.validate(user_id)
    r = types.BaseType(choices=const.ROLE_CHOICE)
    r.validate(new_roles)

    return user_assign_roles(current_app.config, user_id, new_roles)
