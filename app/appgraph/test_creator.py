import uuid

import graphene
from flask import current_app
from gql import gql

from app import validators, const
from app.appgraph.util import get_request_role_userid, ValidationInterface, ValidationResponse
from app.hasura_client import hasura_client


class TestCreatorInterface(graphene.Interface):
    id = graphene.UUID()


class TestCreatorType(graphene.ObjectType):
    class Meta:
        interfaces = (TestCreatorInterface,)


class CreateValidate(graphene.Mutation):
    """Validates test_creator json testrun definition.
    Example json data:
    data:"{\"test_type\":\"set\", \"endpoints\":[{\"name\": \"test\", \"method\": \"get\", \"url\": \"/test\"}]}",
    """

    class Arguments:
        name = graphene.String(
            required=True,
            description='Name.')
        data = graphene.String(
            required=True,
            description='Json data.')
        project_id = graphene.UUID(
            required=True,
            description='Project id to associate with.')
        max_wait = graphene.Int(
            required=True,
            description='Maximum response wait time.')
        min_wait = graphene.Int(
            required=True,
            description='Minimum response wait time.')

    Output = ValidationInterface

    @staticmethod
    def validate(info, name, data, project_id, max_wait, min_wait, validate_unique_name=True):
        project_id = str(project_id)
        role, user_id = get_request_role_userid(info)
        assert user_id, f'unauthenticated request'

        name = validators.validate_text(name)

        gclient = hasura_client(current_app.config)
        # validate configuration exists and user has access to it
        creators = gclient.execute(gql('''
            query ($userId: uuid!, $project_id: uuid!, $name:String!) {
                project (where: {id: {_eq: $project_id}, userProjects: {user_id: {_eq: $userId}}}) {
                    name
                }
                
                test_source(where:{
                    project:{userProjects:{user_id:{_eq:$userId}}}
                    test_creator:{name:{_eq:$name}}
                }) {
                    id
                }
            }
        '''), {
            'userId': user_id,
            'project_id': project_id,
            'name': name,
        })
        assert len(creators['project']) == 1, f'project does not exist'
        if validate_unique_name:
            assert len(creators['test_source']) == 0, f'name {name} is in use'

        # validate configuration body
        validators.validate_test_creator(data, min_wait=min_wait, max_wait=max_wait)

        return {
            'name': name,
            'project_id': project_id,
            'data': data,
            'max_wait': max_wait,
            'min_wait': min_wait,
            'created_by_id': user_id,
        }

    def mutate(self, info, name, data, project_id, max_wait, min_wait):
        CreateValidate.validate(info, name, data, project_id, max_wait, min_wait)
        return ValidationResponse(ok=True)


class Create(CreateValidate):
    """Validates and creates the test_creator json testrun definition."""

    Output = TestCreatorInterface

    def mutate(self, info, name, data, project_id, max_wait, min_wait):
        project_id = str(project_id)
        object_id = str(uuid.uuid4())

        gclient = hasura_client(current_app.config)

        query_params = CreateValidate.validate(info, name, data, project_id, max_wait, min_wait)

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

        return TestCreatorType(id=conf_response['insert_test_creator']['returning'][0]['id'])


class Update(CreateValidate):
    """Validates and updates the test_creator json testrun definition. Returns updated id."""

    class Arguments:
        id = graphene.UUID(
            required=True,
            description='Test creator id.')
        name = graphene.String(
            required=False,
            description='Name.')
        data = graphene.String(
            required=False,
            description='Json data.')
        max_wait = graphene.Int(
            required=False,
            description='Maximum response wait time.')
        min_wait = graphene.Int(
            required=False,
            description='Minimum response wait time.')

    Output = TestCreatorInterface

    def mutate(self, info, id, name=None, data=None, max_wait=None, min_wait=None):
        id = str(id)

        role, user_id = get_request_role_userid(info)
        assert user_id, f'unauthenticated request'

        gclient = hasura_client(current_app.config)

        original = gclient.execute(gql('''query ($objId:uuid!, $userId:uuid!) {
            test_creator (where:{
                    id:{_eq:$objId}
                    project:{userProjects:{user_id:{_eq:$userId}}}
            }) {
                id
                name
                performed
                project_id
                test_source_id
                max_wait
                min_wait
                data
            }
        }'''), variable_values={
            'objId': id,
            'userId': user_id,
        })
        assert len(original['test_creator']) == 1, f'test_creator {id} does not exist'

        original = original['test_creator'][0]
        project_id = original['project_id']
        test_source_id = original['test_source_id']
        new_id = str(uuid.uuid4())

        if not data:
            data = original['data']
        if not name:
            name = original['name']
        if not max_wait:
            max_wait = original['max_wait']
        if not min_wait:
            min_wait = original['min_wait']

        query_params = CreateValidate.validate(info, name, data, project_id, max_wait, min_wait, validate_unique_name=False)

        query_params['id'] = new_id
        query_params['test_source_id'] = test_source_id
        query_params['previous_version_id'] = id

        query = gql('''mutation ($oldId:uuid!, $newId:uuid!, $data:[test_creator_insert_input!]!) {
            insert_test_creator(
                objects: $data
            ) {
                returning { id } 
            }
            update_test_source (
                where:{test_creator_id:{_eq:$oldId}}
                _set:{test_creator_id:$newId}
            ) { affected_rows }
        }''')

        conf_response = gclient.execute(query, variable_values={
            'data': query_params,
            'oldId': id,
            'newId': new_id,
        })
        assert conf_response['insert_test_creator'], f'cannot save creator ({str(conf_response)})'

        return TestCreatorType(id=new_id)
