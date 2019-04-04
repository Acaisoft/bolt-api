import json

import graphene
from flask import current_app

from app import const
from app.appgraph.util import OutputInterfaceFactory, OutputValueFromFactory, get_request_role_userid
from app.services.user_management import user_management
from app.cache import get_cache


class UserInterface(graphene.Interface):
    id = graphene.UUID()
    email = graphene.String()
    project_id = graphene.UUID()
    role = graphene.String()


class UserListItemInterface(graphene.Interface):
    id = graphene.UUID()
    username = graphene.String()
    email_verified = graphene.Boolean()
    email = graphene.String()
    bolt_roles = graphene.List(graphene.String)


class UserListItemType(graphene.ObjectType):
    class Meta:
        interfaces = [UserListItemInterface]


class UserListInterface(graphene.Interface):
    project_id = graphene.UUID()
    users = graphene.List(UserListItemType)


class UserListType(graphene.ObjectType):
    class Meta:
        interfaces = [UserListInterface]


class UserQueries(graphene.ObjectType):

    testrun_user_list = graphene.Field(
        UserListInterface,
        description='Return a list of users in a project.',
        project_id=graphene.UUID(description='Project id to list users of.')
    )

    def resolve_testrun_user_list(self, info, project_id):
        req_role, user_id = get_request_role_userid(info)
        assert user_id, f'unauthenticated request'
        assert req_role in (const.ROLE_ADMIN, const.ROLE_MANAGER), f'user with role {req_role} cannot list users'

        project_id = str(project_id)
        c = get_cache(current_app.config)
        cn = f'resolve_testrun_user_list_{project_id}'
        users = c.get(cn)
        if not users:
            users = user_management.list_users_in_project(project_id)
            c.set(cn, json.dumps(users), 60)
        else:
            users = json.loads(users)

        users_response = [UserListItemType(**x) for x in users]
        return UserListType(project_id=project_id, users=users_response)


class AssignUserToProject(graphene.Mutation):
    """Creates (if needed) and assigns given user to given project with given role."""

    class Arguments:
        email = graphene.String(
            required=True,
            description='User email.')
        project_id = graphene.UUID(
            required=True,
            description='Project ID.')
        role = graphene.String(
            required=True,
            description='User role.')

    Output = OutputInterfaceFactory(UserInterface, 'Assign')

    def mutate(self, info, email, project_id, role):
        req_role, user_id = get_request_role_userid(info)
        assert user_id, f'unauthenticated request'
        assert req_role in (const.ROLE_ADMIN,), f'user with role {req_role} cannot manage users'

        user_id = user_management.user_create(email, str(project_id), role)
        return OutputValueFromFactory(AssignUserToProject, {'returning': [{
            'id': user_id,
            'email': email,
            'project_id': project_id,
            'role': role,
        }]})


class UserAddRole(graphene.Mutation):
    """Grant given user given role"""

    class Arguments:
        user_id = graphene.UUID()
        roles = graphene.List(
            graphene.String,
            description='List of new user roles.')

    Output = OutputInterfaceFactory(UserInterface, 'Roles')

    def mutate(self, info, user_id, roles):
        req_role, req_user_id = get_request_role_userid(info)
        assert req_user_id, f'unauthenticated request'
        assert req_role in (const.ROLE_ADMIN,), f'user with role {req_role} cannot manage roles'

        for r in roles:
            assert r in const.ROLE_CHOICE, f'invalid role: {r}'

        user_id = str(user_id)
        user_data = user_management.user_roles_update(user_id, roles)
        return OutputValueFromFactory(UserAddRole, {'returning': [user_data]})
