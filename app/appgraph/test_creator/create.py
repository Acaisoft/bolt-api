import uuid

from flask import current_app
from gql import gql

from app import const
from app.appgraph.test_creator import types, validate
from app.appgraph.util import OutputInterfaceFactory, OutputValueFromFactory
from app.hasura_client import hasura_client


class Create(validate.Validate):
    """Validates and creates the test_creator json testrun definition."""

    Output = OutputInterfaceFactory(types.TestCreatorInterface, 'Create')

    def mutate(self, info, name, data, project_id, max_wait, min_wait, type_slug):
        project_id = str(project_id)
        object_id = str(uuid.uuid4())

        gclient = hasura_client(current_app.config)

        query_params = validate.Validate.validate(info, name, data, project_id, max_wait, min_wait, type_slug)

        # preset object and test_source id to same id
        query_params['id'] = object_id
        query_params['test_source_id'] = object_id

        query = gql('''mutation ($data:[test_creator_insert_input!]!) {
            insert_test_creator(
                objects: $data
            ) {
                returning { id } 
            }
        }''')

        conf_response = gclient.execute(query, variable_values={'data': query_params})
        assert conf_response['insert_test_creator'], f'cannot save creator ({str(conf_response)})'

        test_source_response = gclient.execute(gql('''mutation ($data:[test_source_insert_input!]!) {
            insert_test_source (objects:$data) {
                affected_rows
            }
        }'''), variable_values={'data': [{
            'id': object_id,
            'project_id': query_params['project_id'],
            'source_type': const.CONF_SOURCE_JSON,
            'test_creator_id': object_id,
        }]})
        assert test_source_response['insert_test_source'].get('affected_rows', 0) == 1, \
            f'cannot save test_source relation ({str(test_source_response)})'

        return OutputValueFromFactory(Create, conf_response['insert_test_creator'])
