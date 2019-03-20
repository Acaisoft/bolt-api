import graphene
from flask import current_app
from gql import gql

from app.appgraph.scaffold import CreateUpdateValidateScaffold
from app.appgraph.util import get_request_role_userid, ValidationInterface, ValidationResponse, OutputValueFromFactory, \
    OutputInterfaceFactory
from app import validators, const
from app.hasura_client import hasura_client


class RepositoryParameterInterface(graphene.InputObjectType):
    name = graphene.String()
    repository_url = graphene.String()
    project_id = graphene.UUID()
    type_slug = graphene.String(description=f'Configuration type: "{const.TESTTYPE_CHOICE}"')


class RepositoryInterface(graphene.Interface):
    id = graphene.UUID()
    name = graphene.String(
        description='Name')
    repository_url = graphene.String(
        description='Repository address')
    project_id = graphene.UUID(
        description='Repository project')
    type_slug = graphene.String(
        description=f'Configuration type: "{const.TESTTYPE_CHOICE}"')


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
        role, user_id = get_request_role_userid(info)
        gclient = hasura_client(current_app.config)

        project_id = str(project_id)

        assert user_id, f'unauthenticated request'
        validators.validate_text(name)

        query = gclient.execute(gql('''query ($projId:uuid!, $repoName:String!, $repoUrl:String!, $userId:uuid!, $confType:uuid!) {
            project(where:{
                id:{_eq:$projId}, 
                userProjects:{user_id:{_eq:$userId}}
            }) { id }
            
            configuration_type(where:{slug_name:{_eq:$confType}}, limit:1) { id }
            
            repository(where:{
                project_id:{_eq:$projId},
                _or:{
                    name:{_eq:$repoName},
                    url:{_eq:$repoUrl}
                }
            }) { id }
            
            }'''), {
            'userId': user_id,
            'repoName': name,
            'repoUrl': repository_url,
            'projId': project_id,
            'confType': type_slug,

        })
        assert len(query.get('repository')) == 0, f'repository with this name or url already exists'

        if role != const.ROLE_ADMIN:
            assert query.get('project'), \
                f'non-admin ({role}) user {user_id} does not have access to project {project_id}'

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

    Output = OutputInterfaceFactory(RepositoryInterface, 'Create')

    def mutate(self, info, name, repository_url, project_id, type_slug):
        gclient = hasura_client(current_app.config)

        query_params = CreateValidate.validate(info, name, repository_url, project_id, type_slug)

        query = gql('''mutation ($data:[repository_insert_input!]!) {
            insert_repository(
                objects: $data
            ) {
                returning { id name repository_url:url project_id type_slug } 
            }
        }''')

        query_response = gclient.execute(query, variable_values={'data': query_params})
        assert query_response['insert_repository'], f'cannot save repository ({str(query_response)})'

        return OutputValueFromFactory(Create, query_response['insert_repository'])


class UpdateValidate(graphene.Mutation):
    """Validates repository configuration."""

    class Arguments:
        id = graphene.UUID()
        name = graphene.String()

    Output = ValidationInterface

    @staticmethod
    def validate(info, id, name):
        role, user_id = get_request_role_userid(info)

        gclient = hasura_client(current_app.config)

        name = validators.validate_text(name)

        query = gclient.execute(gql('''query ($repoName:String!, $userId:uuid!) {
            repository(where:{
                name:{_eq:$repoName},
                project:{userProjects:{user_id:$userId}}
            }) { id }
            
            }'''), variable_values={
            'userId': user_id,
            'repoName': name,

        })
        assert len(query.get('repository')) == 0, f'repository with this name already exists'

        if role != const.ROLE_ADMIN:
            assert query.get('project'), \
                f'non-admin ({role}) user {user_id} does not have access to repository {id}'

        assert len(query.get('configuration_type', [])) == 1, f'configuration type does not exist'

        return {
            'name': name,
        }

    def mutate(self, info, id, name):
        UpdateValidate.validate(info, id, name)
        return ValidationResponse(ok=True)


class Update(UpdateValidate):
    """Validates and updates repository name."""

    Output = OutputInterfaceFactory(RepositoryInterface, 'Update')

    def mutate(self, info, id, name):
        gclient = hasura_client(current_app.config)

        query_params = UpdateValidate.validate(info, id, name)

        query = gql('''mutation ($id:uuid!, $data:repository_set_input!) {
            update_repository(
                where:{id:{_eq:$id}},
                _set: $data
            ) {
                returning { id name } 
            }
        }''')

        query_response = gclient.execute(query, update={'id': str(id), 'data': query_params})
        assert query_response['update_repository'], f'cannot save repository ({str(query_response)})'

        return OutputValueFromFactory(Update, query_response['update_repository'])
