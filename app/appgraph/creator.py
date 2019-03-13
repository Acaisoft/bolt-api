import graphene
from flask import current_app
from gql import gql

from app.appgraph.util import get_request_role_userid, ValidationInterface, ValidationResponse
from bolt_api.upstream.devclient import devclient


class TestCreatorParameterInterface(graphene.InputObjectType):
    value = graphene.String()
    parameter_id = graphene.UUID(name='parameter_id')


class TestCreatorInterface(graphene.Interface):
    id = graphene.UUID()


class TestCreatorType(graphene.ObjectType):
    class Meta:
        interfaces = (TestCreatorInterface,)


class Validate(graphene.Mutation):
    """Validates test_creator json testrun definition."""

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
        role, user_id = get_request_role_userid(info)
        assert user_id, f'unauthenticated request'

        gclient = devclient(current_app.config)

        # validate configuration exists and user has access to it
        creators = gclient.execute(gql('''query ($userId:uuid!, $confId:uuid!) {
            configuration (where:{id:{_eq:$confId}, {project:{userProject:{user_id:{_eq:$userId}}}) {
                name
            }
        }'''), {
            'userId': user_id,
            'confId': configuration_id,
        })
        assert len(creators.get('configuration', None)) == 0, f'configuration does not exist'

        # TODO: validate data, min_/max_wait

        return {
            'data': data,
            'configuration_id': configuration_id,
            'max_wait': max_wait,
            'min_wait': min_wait,
            'created_by_id': user_id,
        }

    def mutate(self, info, name, description, image_url, contact):
        Validate.validate(info, name, description, image_url, contact)
        return ValidationResponse(ok=True)


class Create(Validate):
    """Validates and creates the test_creator json testrun definition."""

    Output = TestCreatorInterface

    def mutate(self, info, name, description, image_url, contact):
        gclient = devclient(current_app.config)

        query_params = Validate.validate(info, name, description, image_url, contact)

        query = gql('''mutation ($data:[test_creator_insert_input!]!) {
            insert_test_creator(
                objects: $data
            ) {
                returning { id } 
            }
        }''')

        conf_response = gclient.execute(query, variable_values={'data': query_params})
        assert conf_response['insert_test_creator'], f'cannot save creator ({str(conf_response)})'

        return TestCreatorType(id=conf_response['insert_test_creator']['returning'][0]['id'])
