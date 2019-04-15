import graphene

from app import const
from app.appgraph.users import types
from app.appgraph.util import OutputInterfaceFactory, OutputValueFromFactory, get_request_role_userid
from app.services.user_management import user_management


class UserRemoveFromProject(graphene.Mutation):
    """Removes given user from given project."""

    class Arguments:
        user_id = graphene.String(
            required=True,
            description='User ID.')
        project_id = graphene.UUID(
            required=True,
            description='Project ID.')

    Output = OutputInterfaceFactory(types.UserInterface, 'Unassign')

    def mutate(self, info, user_id, project_id):
        req_role, req_user_id = get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_MANAGER))

        resp = user_management.user_unassign_from_project(str(user_id), str(project_id))

        return OutputValueFromFactory(UserRemoveFromProject, resp['delete_user_project'])