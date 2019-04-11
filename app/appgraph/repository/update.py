import graphene
from flask import current_app
from gql import gql

from app.appgraph.repository import types
from app.appgraph.util import get_request_role_userid, ValidationInterface, ValidationResponse, OutputValueFromFactory, \
    OutputInterfaceFactory
from app import const
from app.services import validators
from app.hasura_client import hasura_client


class UpdateValidate(graphene.Mutation):
    """Validates repository configuration."""

    class Arguments:
        id = graphene.UUID()
        name = graphene.String(
            required=False)
        repository_url = graphene.String(
            required=False,
            description='Repository address.')
        type_slug = graphene.String(
            required=False,
            description=f'Configuration type: "{const.TESTTYPE_LOAD}"')

    Output = ValidationInterface

    @staticmethod
    def validate(info, id, name=None, repository_url=None, type_slug=None):
        role, user_id = get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_MANAGER, const.ROLE_TESTER))

        gclient = hasura_client(current_app.config)

        if name:
            name = validators.validate_text(name)

        query = gclient.execute(gql('''query ($repoName:String!, $repoUrl:String!, $repoId:uuid!, $userId:uuid!, $confType:String) {
            uniqueName: repository(where:{
                name:{_eq:$repoName},
                project: {userProjects: {user_id: {_eq:$userId}}}
            }) { id }

            uniqueUrl: repository(where:{
                url:{_eq:$repoUrl},
                project: {userProjects: {user_id: {_eq:$userId}}}
            }) { id }

            configuration_type(where:{slug_name:{_eq:$confType}}, limit:1) { id }

            repository(
                where:{
                    id:{_eq:$repoId},
                    project:{userProjects:{user_id:{_eq:$userId}}}
                }
            ) {
                name
                url
                type_slug
                performed
            }

            }'''), variable_values={
            'userId': user_id,
            'repoName': name or '',
            'repoUrl': repository_url or '',
            'repoId': str(id),
            'confType': type_slug or '',

        })
        assert len(query.get('repository')) == 1, f'repository {str(id)} does not exists'

        query_data = {}
        was_performed = query['repository'][0]['performed']

        if name and name != query['repository'][0]['name']:
            assert len(query.get('uniqueName')) == 0, f'repository with this name already exists'
            query_data['name'] = name

        if type_slug and repository_url != query['repository'][0]['type_slug']:
            assert len(query.get('configuration_type',
                                 [])) == 1, f'invalid type_slug "{type_slug}", valid choices are: {const.TESTTYPE_LOAD}'
            assert not was_performed, \
                f'cannot change type_slug, a test has been performed using this repository'
            query_data['type_slug'] = type_slug

        if repository_url and repository_url != query['repository'][0]['url']:
            assert not was_performed, \
                f'cannot change repository_url, a test has been performed using this repository'
            assert len(query.get('uniqueUrl')) == 0, f'repository with this url already exists'
            query_data['url'] = validators.validate_accessibility(current_app.config, repository_url)

        return query_data

    def mutate(self, info, id, name=None, repository_url=None, type_slug=None):
        UpdateValidate.validate(info, id, name, repository_url, type_slug)
        return ValidationResponse(ok=True)


class Update(UpdateValidate):
    """Validates and updates repository name."""

    Output = OutputInterfaceFactory(types.RepositoryInterface, 'Update')

    def mutate(self, info, id, name=None, repository_url=None, type_slug=None):
        gclient = hasura_client(current_app.config)

        query_params = UpdateValidate.validate(info, id, name, repository_url, type_slug)

        query = gql('''mutation ($id:uuid!, $data:repository_set_input!) {
            update_repository(
                where:{id:{_eq:$id}},
                _set: $data
            ) {
                returning { id name repository_url:url project_id type_slug } 
            }
        }''')

        query_response = gclient.execute(query, variable_values={'id': str(id), 'data': query_params})
        assert query_response['update_repository'], f'cannot save repository ({str(query_response)})'

        return OutputValueFromFactory(Update, query_response['update_repository'])
