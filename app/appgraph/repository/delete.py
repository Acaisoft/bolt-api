import graphene
from flask import current_app

from app import const
from app.appgraph.repository import types
from app.appgraph.util import OutputInterfaceFactory, get_request_role_userid, OutputValueFromFactory
from app.services.hasura import hce


class Delete(graphene.Mutation):
    """Soft-deletes a repository."""

    class Arguments:
        pk = graphene.UUID(description='ID of the repo to delete.')

    Output = OutputInterfaceFactory(types.RepositoryInterface, 'Delete')

    def mutate(self, info, pk):
        role, user_id = get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_MANAGER))

        query = '''mutation ($pk:uuid!, $userId:uuid!) {
            update_repository(
                where:{
                    id:{_eq:$pk}
                    is_deleted:{_eq:false}
                    project: {userProjects: {user_id: {_eq:$userId}}}
                },
                _set: {is_deleted:true}
            ) {
                affected_rows
                returning { id name repository_url:url project_id type_slug } 
            }
        }'''

        query_response = hce(current_app.config, query, {
            'pk': str(pk),
            'userId': user_id,
        })
        assert query_response['update_repository'] and query_response['update_repository']['affected_rows'] == 1, \
            f'repository not found ({str(query_response)})'

        return OutputValueFromFactory(Delete, query_response['update_repository'])
