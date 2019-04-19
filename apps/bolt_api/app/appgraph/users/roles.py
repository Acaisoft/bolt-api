import graphene

from services import const, gql_util
from apps.bolt_api.app.appgraph.users import types
from services.user_management import user_management


class UserAddRole(graphene.Mutation):
    """Grant given user given role"""

    class Arguments:
        user_id = graphene.UUID()
        roles = graphene.List(
            graphene.String,
            description='List of new user roles.')

    Output = gql_util.OutputInterfaceFactory(types.UserInterface, 'Roles')

    def mutate(self, info, user_id, roles):
        req_role, req_user_id = gql_util.get_request_role_userid(info, (const.ROLE_ADMIN,))

        for r in roles:
            assert r in const.ROLE_CHOICE, f'invalid role: {r}'

        user_id = str(user_id)
        user_data = user_management.user_roles_update(user_id, roles)
        return gql_util.OutputValueFromFactory(UserAddRole, {'returning': [user_data]})