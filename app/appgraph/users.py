import graphene

from app import const
from app.appgraph.util import OutputInterfaceFactory, OutputValueFromFactory, get_request_role_userid
from app.auth import user_management


class UserInterface(graphene.Interface):
    id = graphene.UUID()
    email = graphene.String()
    project_id = graphene.UUID()
    role = graphene.String()


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

    Output = OutputInterfaceFactory(UserInterface, 'Create')

    def mutate(self, info, email, project_id, role):

        req_role, user_id = get_request_role_userid(info)
        assert user_id, f'unauthenticated request'
        assert req_role in (const.ROLE_ADMIN, const.ROLE_MANAGER), f'user with role {req_role} cannot update projects'

        user_id = user_management.user_create(email, str(project_id), role)
        return OutputValueFromFactory(AssignUserToProject, {'returning': [{
            'id': user_id,
            'email': email,
            'project_id': project_id,
            'role': role,
        }]})
