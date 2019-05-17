import graphene

from services import const, gql_util
from apps.bolt_api.app.appgraph.users import types
from services.user_management import user_management


class UserRemoveFromProject(graphene.Mutation):
    """Removes given user from given project."""

    class Arguments:
        user_id = graphene.String(
            required=True,
            description='User ID.')
        project_id = graphene.UUID(
            required=True,
            description='Project ID.')

    Output = gql_util.OutputInterfaceFactory(types.UserInterface, 'Unassign')

    def mutate(self, info, user_id, project_id):
        req_role, req_user_id = gql_util.get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_TENANT_ADMIN, const.ROLE_MANAGER))

        resp = user_management.user_unassign_from_project(str(user_id), str(project_id))

        return gql_util.OutputValueFromFactory(UserRemoveFromProject, resp['delete_user_project'])