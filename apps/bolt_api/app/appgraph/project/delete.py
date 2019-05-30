import graphene
from flask import current_app

from apps.bolt_api.app.appgraph.project import types
from services import const, gql_util
from services.hasura import hce


class Delete(graphene.Mutation):
    """Soft-deletes a project."""

    class Arguments:
        pk = graphene.UUID(description='ID of the project to delete.')

    Output = gql_util.OutputInterfaceFactory(types.ProjectInterface, 'Delete')

    def mutate(self, info, pk):
        _, user_id = gql_util.get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_TENANT_ADMIN))

        query = '''mutation ($pk:uuid!, $userId:uuid!) {
            update_project(
                where:{
                    id:{_eq:$pk}
                    is_deleted:{_eq:false}
                    userProjects: {user_id: {_eq:$userId}}
                },
                _set: {is_deleted:true}
            ) {
                affected_rows
                returning { id name description image_url } 
            }
        }'''

        query_response = hce(current_app.config, query, {
            'pk': str(pk),
            'userId': user_id,
        })
        assert query_response['update_project'] and query_response['update_project']['affected_rows'] == 1, \
            f'project not found ({str(query_response)})'

        return gql_util.OutputValueFromFactory(Delete, query_response['update_project'])
