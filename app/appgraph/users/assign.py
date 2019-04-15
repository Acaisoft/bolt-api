import graphene

from app import const
from app.appgraph.users import types
from app.appgraph.util import OutputInterfaceFactory, OutputValueFromFactory, get_request_role_userid
from app.services.user_management import user_management


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

    Output = OutputInterfaceFactory(types.UserInterface, 'Assign')

    def mutate(self, info, email, project_id, role):
        req_role, user_id = get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_MANAGER))

        user_id = user_management.user_create(email, str(project_id), role)
        return OutputValueFromFactory(UserAssignToProject, {'returning': [{
            'id': user_id,
            'email': email,
            'project_id': project_id,
            'role': role,
        }]})