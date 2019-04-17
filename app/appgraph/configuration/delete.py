import graphene
from flask import current_app

from app.appgraph.configuration import types
from app.appgraph.util import get_request_role_userid, OutputTypeFactory, OutputValueFromFactory
from app import const
from app.services.hasura import hce


class Delete(graphene.Mutation):
    """Soft-deletes a configuration."""

    class Arguments:
        pk = graphene.UUID(description='ID of the project to delete.')

    Output = OutputTypeFactory(types.ConfigurationType, 'Delete')

    def mutate(self, info, pk):
        _, user_id = get_request_role_userid(info, (const.ROLE_ADMIN,))

        query = '''mutation ($pk:uuid!, $userId:uuid!) {
            update_configuration(
                where:{
                    id:{_eq:$pk}
                    is_deleted:{_eq:false}
                    project:{
                        userProjects: {user_id: {_eq:$userId}},
                        is_deleted: {_eq:false}
                    }
                },
                _set: {is_deleted:true}
            ) {
                affected_rows
                returning { id name type_slug project_id test_source_id } 
            }
        }'''

        query_response = hce(current_app.config, query, {
            'pk': str(pk),
            'userId': user_id,
        })
        assert query_response['update_configuration'] and query_response['update_configuration']['affected_rows'] == 1, \
            f'configuration not found ({str(query_response)})'

        return OutputValueFromFactory(Delete, query_response['update_configuration'])
