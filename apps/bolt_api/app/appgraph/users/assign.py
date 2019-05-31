import graphene

from services import const, gql_util
from apps.bolt_api.app.appgraph.users import types
from services.user_management import user_management


class UserAssignToProject(graphene.Mutation):
    """Creates (if needed) and assigns given user to given project with given role."""

    class Arguments:
        email = graphene.String(
            required=True,
            description='User email.')
        role = graphene.String(
            required=True,
            description='User role.')
        project_id = graphene.UUID(
            required=False,
            description='Project ID.')

    Output = gql_util.OutputInterfaceFactory(types.UserInterface, 'Assign')

    def mutate(self, info, email, role, project_id=None):
        req_role, req_user_id = gql_util.get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_TENANT_ADMIN, const.ROLE_MANAGER))

        if not project_id:
            assert role == const.ROLE_TENANT_ADMIN, f'user without a project must have "tenantadmin" role'
            assert req_role == const.ROLE_ADMIN, f'only superadmin may create tenantadmins'
        else:
            project_id = str(project_id)

        user_id = user_management.user_create(email, role, project_id)

        return gql_util.OutputValueFromFactory(UserAssignToProject, {'returning': [{
            'id': user_id,
            'email': email,
            'project_id': project_id,
            'role': role,
        }]})
