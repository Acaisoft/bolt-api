import graphene
from flask import current_app

from app.appgraph.project import types
from app.appgraph.util import get_request_role_userid, OutputValueFromFactory, OutputInterfaceFactory
from app import const
from app.services.hasura import hce


class Delete(graphene.Mutation):
    """Soft-deletes a project."""

    class Arguments:
        pk = graphene.UUID(description='ID of the project to delete.')

    Output = OutputInterfaceFactory(types.ProjectInterface, 'Delete')

    def mutate(self, info, pk):
        _, user_id = get_request_role_userid(info, (const.ROLE_ADMIN,))

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

        return OutputValueFromFactory(Delete, query_response['update_project'])
