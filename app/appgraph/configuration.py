import json

import graphene
from flask import current_app
from gql import gql

from app.appgraph.util import get_request_role_userid, ValidationInterface, ValidationResponse, OutputTypeFactory, \
    OutputValueFactory
from app import validators, const
from app.hasura_client import hasura_client


class ConfigurationParameterAbstractType(graphene.AbstractType):
    value = graphene.String()
    parameter_id = graphene.UUID(name='parameter_id')


class ConfigurationParameterInterface(ConfigurationParameterAbstractType, graphene.Interface):
    pass


class ConfigurationParameterInput(ConfigurationParameterAbstractType, graphene.InputObjectType):
    pass


class ConfigurationParameterType(graphene.ObjectType):
    class Meta:
        interfaces = (ConfigurationParameterInterface,)


class ConfigurationInterface(graphene.Interface):
    id = graphene.UUID()
    name = graphene.String()
    type_slug = graphene.String(
        description=f'Configuration type: "{const.TESTTYPE_LOAD}"')
    code_source = graphene.String(
        description=f'Test code source: "{const.CONF_SOURCE_JSON}" or "{const.CONF_SOURCE_REPO}"')
    repository_id = graphene.String(
        description='Repository to fetch test definition from.')
    project_id = graphene.UUID()
    configuration_parameters = graphene.List(
        ConfigurationParameterInterface,
        description='Default parameter types overrides.')


class ConfigurationType(graphene.ObjectType):
    class Meta:
        interfaces = (ConfigurationInterface,)


class CreateValidate(graphene.Mutation):
    """Validates configuration for a testrun. Ensures repository is accessible and test parameters are sane."""

    class Arguments:
        name = graphene.String(
            required=True,
            description='Name, not unique.')
        type_slug = graphene.String(
            required=True,
            description=f'Configuration type: "{const.TESTTYPE_LOAD}"')
        code_source = graphene.String(
            required=True,
            description=f'Test code source: "{const.CONF_SOURCE_JSON}" or "{const.CONF_SOURCE_REPO}"')
        project_id = graphene.UUID(
            required=True,
            description='Project to create test in, user must have access to it.')
        repository_id = graphene.String(
            required=False,
            description='Repository to fetch test definition from.')
        configuration_parameters = graphene.List(
            ConfigurationParameterInput,
            required=False,
            description='Default parameter types overrides.')

    Output = ValidationInterface

    @staticmethod
    def validate(info, name, type_slug, code_source, project_id, repository_id=None, configuration_parameters=None):
        project_id = str(project_id)

        assert code_source in const.CONF_SOURCE_CHOICE, f'invalid choice of code_source (valid choices: {const.CONF_SOURCE_CHOICE})'

        assert type_slug in const.TESTTYPE_CHOICE, f'invalid choice of type_slug (valid choices: {const.TESTTYPE_CHOICE})'

        role, user_id = get_request_role_userid(info)
        assert user_id, f'unauthenticated request'

        gclient = hasura_client(current_app.config)

        repo_query = {
            'type_slug': type_slug,
            'confName': name,
            'projId': project_id,
            'userId': user_id,
            'repoId': repository_id or "",
            'fetchRepo': bool(repository_id),
        }

        repo = gclient.execute(gql('''query ($confName:String, $repoId:uuid!, $fetchRepo:Boolean!, $projId:uuid!, $userId:uuid!, $type_slug:String!) {
            repository_by_pk (id:$repoId) @include(if:$fetchRepo) {
                url
                configuration_type { slug_name }
                project {
                    is_deleted
                    userProjects { user_id }
                }
            }
            
            parameter (where:{configurationTypes:{slug_name:{_eq:$type_slug}}}) {
                id
                default_value
                param_name
                name
            }
            
            user_project (where:{ user_id:{_eq:$userId}, project_id:{_eq:$projId} }) {
                id
            }
            
            project_by_pk (id:$projId) {
                id
            }
            
            configuration (where:{name:{_eq:$confName}, project:{userProjects:{user_id:{_eq:$userId}}}}) {
                id
            }
        }'''), repo_query)

        if role != const.ROLE_ADMIN:
            assert repo.get('user_project', None), \
                f'non-admin ({role}) user {user_id} does not have access to project {project_id}'

        validators.validate_text(name)

        assert repo.get('project_by_pk', None), f'project "{project_id}" does not exist'

        assert len(repo.get('configuration', [])) == 0, f'configuration named "{name}" already exists'

        query_data = {
            'name': name,
            'project_id': project_id,
        }

        if user_id:
            query_data['created_by_id'] = user_id

        if type_slug:
            query_data['type_slug'] = type_slug

        if repository_id and code_source == const.CONF_SOURCE_REPO:
            assert repo.get('repository_by_pk', None), f'repository does not exist'
            validators.validate_repository(user_id=user_id, repo_config=repo['repository_by_pk'])
            validators.validate_accessibility(current_app.config, repo['repository_by_pk']['url'])
            query_data['repository_id'] = str(repository_id)

        if configuration_parameters:
            patched_params = validators.validate_test_params(configuration_parameters, defaults=repo['parameter'])
            if patched_params:
                query_data['configuration_parameters'] = {'data': []}
                for param_id, param_value in patched_params.items():
                    query_data['configuration_parameters']['data'].append({
                        'parameter_id': param_id,
                        'value': param_value,
                    })

        return query_data

    def mutate(self, info, name, type_slug, code_source, project_id, repository_id=None, configuration_parameters=None):
        CreateValidate.validate(info, name, type_slug, code_source, project_id, repository_id, configuration_parameters)
        return ValidationResponse(ok=True)


class Create(CreateValidate):
    """Validates and saves configuration for a testrun."""

    Output = OutputTypeFactory(ConfigurationType, 'Create')

    def mutate(self, info, name, type_slug, code_source, project_id, repository_id=None, configuration_parameters=None):
        gclient = hasura_client(current_app.config)

        query_params = CreateValidate.validate(info, name, type_slug, code_source, project_id, repository_id, configuration_parameters)

        query = gql('''mutation ($data:[configuration_insert_input!]!) {
            insert_configuration(
                objects: $data
            ) {
                returning { id name code_source type_slug repository_id project_id } 
            }
        }''')

        conf_response = gclient.execute(query, variable_values={'data': query_params})
        assert conf_response['insert_configuration'], f'cannot save configuration ({str(conf_response)})'

        return OutputValueFactory(Create, conf_response['insert_configuration'])


class UpdateValidate(graphene.Mutation):
    """Updates configuration for a testrun.
    All fields are optional.
    Only name can be updated if configuration testrun has been performed.
    """

    class Arguments():
        id = graphene.UUID(
            description='Configuration object id')
        name = graphene.String(
            required=False,
            description='Name, not unique.')
        type_slug = graphene.String(
            required=False,
            description=f'Configuration type: "{const.TESTTYPE_LOAD}"')
        code_source = graphene.String(
            required=False,
            description=f'Test code source (choices: {const.CONF_SOURCE_CHOICE})')
        repository_id = graphene.String(
            required=False,
            description='Repository to fetch test definition from.')
        configuration_parameters = graphene.List(
            ConfigurationParameterInput,
            required=False,
            description='Default parameter types overrides.')

    Output = ValidationInterface

    @staticmethod
    def validate(info, id, name=None, type_slug=None, code_source=None, repository_id=None, configuration_parameters=None):

        gclient = hasura_client(current_app.config)

        original = gclient.execute(gql('''query ($confId:uuid!) {
            configuration_by_pk (id:$confId) {
                performed
                name
                code_source
                type_slug
                project_id
                repository_id
            }
        }'''), {'confId': str(id)})
        assert original['configuration_by_pk'], f'configuration does not exist'

        is_performed = original['configuration_by_pk']['performed']
        if is_performed:
            assert not any((type_slug, code_source, repository_id, configuration_parameters)), \
                f'configuration {str(id)} has already been performed, only name is editable'

        role, user_id = get_request_role_userid(info)
        assert user_id, f'unauthenticated request'

        if name:
            validators.validate_text(name)

        if type_slug:
            assert type_slug in const.TESTTYPE_CHOICE, \
                f'invalid choice of type_slug (valid choices: {const.TESTTYPE_CHOICE})'
        else:
            type_slug = original['configuration_by_pk']['type_slug']

        if code_source:
            assert code_source in const.CONF_SOURCE_CHOICE, \
                f'invalid choice of code_source (valid choices: {const.CONF_SOURCE_CHOICE})'

        repo_query = {
            'type_slug': type_slug,
            'confId': str(id),
            'confName': name or '',
            'userId': user_id,
            'repoId': repository_id or '',
            'fetchRepo': bool(repository_id),
        }


        repo = gclient.execute(gql('''query ($confId:uuid!, $confName:String, $repoId:uuid!, $fetchRepo:Boolean!, $userId:uuid!, $type_slug:String!) {
            repository_by_pk (id:$repoId) @include(if:$fetchRepo) {
                url
                configuration_type { slug_name }
                project {
                    is_deleted
                    userProjects { user_id }
                }
            }
            
            parameter (where:{configurationTypes:{slug_name:{_eq:$type_slug}}}) {
                id
                default_value
                param_name
                name
            }
                        
            isNameUnique: configuration (where:{name:{_eq:$confName}, project:{userProjects:{user_id:{_eq:$userId}}}}) {
                id
            }
            
            hasUserAccess: configuration (where:{id:{_eq:$confId}, project:{userProjects:{user_id:{_eq:$userId}}}}) {
                id
            }
        }'''), repo_query)

        if role != const.ROLE_ADMIN:
            assert repo.get('hasUserAccess', None), \
                f'non-admin ({role}) user {user_id} does not have access to configuration {str(id)}'

        query_data = {}

        if name:
            validators.validate_text(name)
            assert len(repo.get('isNameUnique', [])) == 0, f'configuration named "{name}" already exists'
            query_data['name'] = name

        if type_slug:
            query_data['type_slug'] = type_slug

        if code_source:
            query_data['code_source'] = code_source
        else:
            code_source = original['configuration_by_pk']['code_source']

        if repository_id and code_source != const.CONF_SOURCE_REPO:
            assert False, f'cannot set repository_id on a "{code_source}" type configuration'

        if repository_id and code_source == const.CONF_SOURCE_REPO:
            assert repo.get('repository_by_pk', None), f'repository does not exist'
            validators.validate_repository(user_id=user_id, repo_config=repo['repository_by_pk'])
            validators.validate_accessibility(current_app.config, repo['repository_by_pk']['url'])
            query_data['repository_id'] = repository_id

        if configuration_parameters:
            patched_params = validators.validate_test_params(configuration_parameters, defaults=repo['parameter'])
            if patched_params:
                query_data['configuration_parameters'] = {'data': []}
                for param_id, param_value in patched_params.items():
                    query_data['configuration_parameters']['data'].append({
                        'parameter_id': param_id,
                        'value': param_value,
                    })

        return query_data

    def mutate(self, info, id, name=None, type_slug=None, code_source=None, repository_id=None, configuration_parameters=None):
        UpdateValidate.validate(info, id, name, type_slug, code_source, repository_id, configuration_parameters)
        return ValidationResponse(ok=True)


class Update(UpdateValidate):
    """Validates and saves configuration for a testrun."""

    Output = OutputTypeFactory(ConfigurationType, 'Update')

    def mutate(self, info, id, name=None, type_slug=None, code_source=None, repository_id=None, configuration_parameters=None):
        gclient = hasura_client(current_app.config)

        query_params = UpdateValidate.validate(info, id, name, type_slug, code_source, repository_id,
                                               configuration_parameters)

        query = gql('''mutation ($id:uuid!, $data:configuration_set_input!) {
            update_configuration(
                where:{id:{_eq:$id}},
                _set: $data
            ) {
                returning { id name code_source type_slug repository_id project_id } 
            }
        }''')

        conf_response = gclient.execute(query, variable_values={'id': str(id), 'data': query_params})
        assert conf_response['update_configuration'], f'cannot update configuration ({str(conf_response)})'

        return OutputValueFactory(Update, conf_response['update_configuration'])
