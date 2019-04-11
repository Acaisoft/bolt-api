import uuid
import graphene
from flask import current_app
from gql import gql

from app.appgraph.repository import types
from app.appgraph.util import get_request_role_userid, ValidationInterface, ValidationResponse, OutputValueFromFactory, \
    OutputInterfaceFactory
from app import const
from app.services import validators
from app.hasura_client import hasura_client


class CreateValidate(graphene.Mutation):
    """Validates repository configuration."""

    class Arguments:
        name = graphene.String(
            required=True,
            description='Name, unique in this project.')
        repository_url = graphene.String(
            required=True,
            description='Repository address.')
        project_id = graphene.UUID(
            required=True,
            description='Repository project.')
        type_slug = graphene.String(
            required=True,
            description=f'Configuration type: "{const.TESTTYPE_LOAD}"')

    Output = ValidationInterface

    @staticmethod
    def validate(info, name, repository_url, project_id, type_slug):
        role, user_id = get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_MANAGER, const.ROLE_TESTER))

        gclient = hasura_client(current_app.config)

        project_id = str(project_id)

        name = validators.validate_text(name)

        query = gclient.execute(gql('''query ($projId:uuid!, $repoName:String!, $repoUrl:String!, $userId:uuid!, $confType:uuid!) {
            project(where:{
                id:{_eq:$projId}, 
                userProjects:{user_id:{_eq:$userId}}
            }) { id }
            
            configuration_type(where:{slug_name:{_eq:$confType}}, limit:1) { id }
            
            uniqueName: repository(where:{
                project_id:{_eq:$projId},
                name:{_eq:$repoName}
            }) { id }
            
            uniqueUrl: repository(where:{
                project_id:{_eq:$projId},
                url:{_eq:$repoUrl}
            }) { id }
            
            }'''), {
            'userId': user_id,
            'repoName': name,
            'repoUrl': repository_url,
            'projId': project_id,
            'confType': type_slug,

        })
        assert query.get('project'), f'project does not exist'

        assert len(query.get('uniqueName')) == 0, f'repository with this name already exists'

        assert len(query.get('uniqueUrl')) == 0, f'repository with this url already exists'

        assert len(query.get('configuration_type', [])) == 1, f'configuration type does not exist'

        validators.validate_accessibility(current_app.config, repository_url)

        return {
            'name': name,
            'url': repository_url,
            'project_id': project_id,
            'type_slug': type_slug,
            'created_by_id': user_id,
        }

    def mutate(self, info, name, repository_url, project_id, type_slug):
        CreateValidate.validate(info, name, repository_url, project_id, type_slug)
        return ValidationResponse(ok=True)


class Create(CreateValidate):
    """Validates and creates a repository."""

    Output = OutputInterfaceFactory(types.RepositoryInterface, 'Create')

    def mutate(self, info, name, repository_url, project_id, type_slug):
        gclient = hasura_client(current_app.config)

        query_params = CreateValidate.validate(info, name, repository_url, project_id, type_slug)
        query_params['id'] = str(uuid.uuid4())
        test_source_params = {
            'id': query_params['id'],
            'project_id': query_params['project_id'],
            'source_type': const.CONF_SOURCE_REPO,
            'repository_id': query_params['id'],
        }

        query = gql('''mutation ($data:[repository_insert_input!]!, $test_source_params:test_source_insert_input!) {
            insert_repository(
                objects: $data
            ) {
                returning { id name repository_url:url project_id type_slug } 
            }
            insert_test_source (objects:[$test_source_params]) {
                returning { id }
            }
        }''')

        query_response = gclient.execute(query, variable_values={
            'data': query_params,
            'test_source_params': test_source_params,
        })
        assert query_response['insert_repository'], f'cannot save repository ({str(query_response)})'

        return OutputValueFromFactory(Create, query_response['insert_repository'])
