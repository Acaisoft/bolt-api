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
        project_id = graphene.UUID(
            required=True,
            description='Project ID.')
        role = graphene.String(
            required=True,
            description='User role.')

    Output = gql_util.OutputInterfaceFactory(types.UserInterface, 'Assign')

    def mutate(self, info, email, project_id, role):
        req_role, req_user_id = gql_util.get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_TENANT_ADMIN, const.ROLE_MANAGER))

        user_id = user_management.user_create(email, str(project_id), role)

        return gql_util.OutputValueFromFactory(UserAssignToProject, {'returning': [{
            'id': user_id,
            'email': email,
            'project_id': project_id,
            'role': role,
        }]})