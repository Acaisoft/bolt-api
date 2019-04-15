import graphene

from app import const
from app.appgraph.users import types
from app.appgraph.util import OutputInterfaceFactory, OutputValueFromFactory, get_request_role_userid
from app.services.user_management import user_management


class UserAddRole(graphene.Mutation):
    """Grant given user given role"""

    class Arguments:
        user_id = graphene.UUID()
        roles = graphene.List(
            graphene.String,
            description='List of new user roles.')

    Output = OutputInterfaceFactory(types.UserInterface, 'Roles')

    def mutate(self, info, user_id, roles):
        req_role, req_user_id = get_request_role_userid(info, (const.ROLE_ADMIN,))

        for r in roles:
            assert r in const.ROLE_CHOICE, f'invalid role: {r}'

        user_id = str(user_id)
        user_data = user_management.user_roles_update(user_id, roles)
        return OutputValueFromFactory(UserAddRole, {'returning': [user_data]})