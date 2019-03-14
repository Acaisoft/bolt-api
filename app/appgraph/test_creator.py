import graphene
from flask import current_app
from gql import gql

from app import validators
from app.appgraph.util import get_request_role_userid, ValidationInterface, ValidationResponse
from app.hasura_client import hasura_client


class TestCreatorInterface(graphene.Interface):
    id = graphene.UUID()


class TestCreatorType(graphene.ObjectType):
    class Meta:
        interfaces = (TestCreatorInterface,)


class Validate(graphene.Mutation):
    """Validates test_creator json testrun definition.
    Example json data:
    data:"{\"test_type\":\"set\", \"endpoints\":[{\"name\": \"test\", \"method\": \"get\", \"url\": \"/test\"}]}",
    """

    class Arguments:
        data = graphene.String(
            required=True,
            description='Json data.')
        configuration_id = graphene.UUID(
            required=True,
            description='Existing configuration.')
        max_wait = graphene.Int(
            required=True,
            description='Maximum response wait time.')
        min_wait = graphene.Int(
            required=True,
            description='Minimum response wait time.')

    Output = ValidationInterface

    @staticmethod
    def validate(info, data, configuration_id, max_wait, min_wait):
        configuration_id = str(configuration_id)
        role, user_id = get_request_role_userid(info)
        assert user_id, f'unauthenticated request'

        gclient = hasura_client(current_app.config)
        # validate configuration exists and user has access to it
        creators = gclient.execute(gql('''
            query ($userId: uuid!, $confId: uuid!) {
                configuration(where: {id: {_eq: $confId}, project: {userProjects: {user_id: {_eq: $userId}}}}) {
                    name
                }
            }
        '''), {
            'userId': user_id,
            'confId': configuration_id
        })
        assert len(creators['configuration']) == 1, f'configuration does not exist'

        # validate configuration body
        validators.validate_test_creator(data, min_wait=min_wait, max_wait=max_wait)

        return {
            'data': data,
            'max_wait': max_wait,
            'min_wait': min_wait,
            'created_by_id': user_id,
        }

    def mutate(self, info, data, configuration_id, max_wait, min_wait):
        Validate.validate(info, data, configuration_id, max_wait, min_wait)
        return ValidationResponse(ok=True)


class Create(Validate):
    """Validates and creates the test_creator json testrun definition."""

    Output = TestCreatorInterface

    def mutate(self, info, data, configuration_id, max_wait, min_wait):
        configuration_id = str(configuration_id)

        gclient = hasura_client(current_app.config)

        query_params = Validate.validate(info, data, configuration_id, max_wait, min_wait)

        query = gql('''mutation ($data:[test_creator_insert_input!]!) {
            insert_test_creator(
                objects: $data
            ) {
                returning { id } 
            }
        }''')

        conf_response = gclient.execute(query, variable_values={'data': query_params})
        assert conf_response['insert_test_creator'], f'cannot save creator ({str(conf_response)})'

        test_creator_id = conf_response['insert_test_creator']['returning'][0].get('id')

        m2m_response = gclient.execute(gql('''mutation ($data:[test_creator_configuration_m2m_insert_input!]!) {
            insert_test_creator_configuration_m2m (objects:$data) {
                affected_rows
            }
        }'''), variable_values={'data': [{
            'configuration_id': configuration_id,
            'test_creator_id': test_creator_id,
        }]})
        assert m2m_response['insert_test_creator_configuration_m2m'].get('affected_rows', 0) == 1, \
            f'cannot save m2m relation ({str(m2m_response)})'

        return TestCreatorType(id=conf_response['insert_test_creator']['returning'][0]['id'])
