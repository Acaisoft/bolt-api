import graphene
import math
from flask import current_app
from gql import gql

from app.appgraph.util import get_request_role_userid, ValidationInterface, ValidationResponse, OutputTypeFactory, \
    OutputValueFromFactory
from app import const
from app.services import validators
from app.hasura_client import hasura_client


class ConfigurationParameterAbstractType(graphene.AbstractType):
    value = graphene.String()
    parameter_slug = graphene.String()


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
    project_id = graphene.UUID()
    test_source_id = graphene.UUID(
        required=False,
        description='Test source to fetch test definition from.')
    configuration_parameters = graphene.List(
        ConfigurationParameterInterface,
        description='Default parameter types overrides.')


class ConfigurationType(graphene.ObjectType):
    class Meta:
        interfaces = (ConfigurationInterface,)
    configuration_parameters = graphene.List(
        ConfigurationParameterType,
        description='Default parameter types overrides.')


class CreateValidate(graphene.Mutation):
    """Validates configuration for a testrun. Ensures repository is accessible and test parameters are sane."""

    class Arguments:
        name = graphene.String(
            required=True,
            description='Name, not unique.')
        type_slug = graphene.String(
            required=True,
            description=f'Configuration type: "{const.TESTTYPE_LOAD}"')
        project_id = graphene.UUID(
            required=True,
            description='Project to create test in, user must have access to it.')
        test_source_id = graphene.UUID(
            required=False,
            description='Test source to fetch test definition from.')
        configuration_parameters = graphene.List(
            ConfigurationParameterInput,
            required=True,
            description='Default parameter types overrides.')

    Output = ValidationInterface

    @staticmethod
    def validate(info, name, type_slug, project_id, test_source_id=None, configuration_parameters=None):
        project_id = str(project_id)

        assert type_slug in const.TESTTYPE_CHOICE, f'invalid choice of type_slug (valid choices: {const.TESTTYPE_CHOICE})'

        name = validators.validate_text(name)

        role, user_id = get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_MANAGER, const.ROLE_TESTER))

        gclient = hasura_client(current_app.config)

        repo_query = {
            'type_slug': type_slug,
            'confName': name,
            'projId': project_id,
            'userId': user_id,
            'sourceId': str(test_source_id) or "",
            'fetchSource': bool(test_source_id),
        }

        repo = gclient.execute(gql('''query (
                $confName:String, $sourceId:uuid!, $fetchSource:Boolean!, 
                $projId:uuid!, $userId:uuid!, $type_slug:String!
        ) {
            test_source (where:{
                    id:{_eq:$sourceId}, 
                    project:{userProjects:{user_id:{_eq:$userId}}}
            }) @include(if:$fetchSource) {
                source_type
                project {
                    userProjects { user_id }
                }
                repository {
                    name
                    url
                    configuration_type { slug_name }
                    project {
                        userProjects { user_id }
                    }
                }
                test_creator {
                    name
                    data
                    min_wait
                    max_wait
                    project {
                        userProjects { user_id }
                    }
                }
            }
            
            parameter (where:{configuration_type:{slug_name:{_eq:$type_slug}}}) {
                slug_name
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
            
            configuration (where:{
                name:{_eq:$confName}, 
                project_id:{_eq:$projId}, 
                project:{userProjects:{user_id:{_eq:$userId}}}
            }) {
                id
            }
        }'''), repo_query)

        if role != const.ROLE_ADMIN:
            assert repo.get('user_project', None), \
                f'non-admin ({role}) user {user_id} does not have access to project {project_id}'

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

        patched_params = validators.validate_test_params(configuration_parameters, defaults=repo['parameter'])
        if patched_params:
            query_data['configuration_parameters'] = {'data': []}
            for parameter_slug, param_value in patched_params.items():
                query_data['configuration_parameters']['data'].append({
                    'parameter_slug': parameter_slug,
                    'value': param_value,
                })
                # calculate instances number based on num of users
                if parameter_slug == const.TESTPARAM_USERS:
                    query_data['instances'] = math.ceil(int(param_value) / const.TESTRUN_MAX_USERS_PER_INSTANCE)

        if test_source_id:
            test_source = repo.get('test_source')
            assert len(test_source), f'test_source {str(test_source_id)} does not exist'
            test_source = test_source[0]

            if test_source['source_type'] == const.CONF_SOURCE_REPO:
                assert test_source.get('repository', None), f'repository does not exist'
                validators.validate_repository(user_id=user_id, repo_config=test_source['repository'])
                validators.validate_accessibility(current_app.config, test_source['repository']['url'])
                query_data['test_source_id'] = str(test_source_id)
            elif test_source['source_type'] == const.CONF_SOURCE_JSON:
                assert test_source.get('test_creator', None), f'test_creator does not exist'
                validators.validate_test_creator(
                    test_source['test_creator']['data'],
                    min_wait=test_source['test_creator']['min_wait'],
                    max_wait=test_source['test_creator']['max_wait']
                )
                query_data['test_source_id'] = str(test_source_id)
            else:
                raise AssertionError(f'test source {str(test_source_id)} is invalid: {test_source["source_type"]}')

        return query_data

    def mutate(self, info, name, type_slug, project_id, test_source_id=None, configuration_parameters=None):
        CreateValidate.validate(info, name, type_slug, project_id, test_source_id, configuration_parameters)
        return ValidationResponse(ok=True)


class Create(CreateValidate):
    """Validates and saves configuration for a testrun."""

    Output = OutputTypeFactory(ConfigurationType, 'Create')

    def mutate(self, info, name, type_slug, project_id, test_source_id=None, configuration_parameters=None):
        gclient = hasura_client(current_app.config)

        query_params = CreateValidate.validate(info, name, type_slug, project_id, test_source_id, configuration_parameters)

        query = gql('''mutation ($data:[configuration_insert_input!]!) {
            insert_configuration(
                objects: $data
            ) {
                returning { 
                    id name type_slug project_id test_source_id 
                } 
            }
        }''')

        conf_response = gclient.execute(query, variable_values={'data': query_params})
        assert conf_response['insert_configuration'], f'cannot save configuration ({str(conf_response)})'

        return OutputValueFromFactory(Create, conf_response['insert_configuration'])


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
        test_source_id = graphene.UUID(
            required=False,
            description='Test source to fetch test definition from.')
        configuration_parameters = graphene.List(
            ConfigurationParameterInput,
            required=False,
            description='Default parameter types overrides.')

    Output = ValidationInterface

    @staticmethod
    def validate(info, id, name=None, type_slug=None, test_source_id=None, configuration_parameters=None):

        role, user_id = get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_MANAGER, const.ROLE_TESTER))

        gclient = hasura_client(current_app.config)

        original = gclient.execute(gql('''query ($confId:uuid!, $userId:uuid!) {
            configuration (where:{id:{_eq:$confId}, project:{userProjects:{user_id:{_eq:$userId}}}}) {
                performed
                name
                type_slug
                project_id
                test_source_id
            }
        }'''), {'confId': str(id), 'userId': user_id})
        assert len(original['configuration']), f'configuration does not exist'

        is_performed = original['configuration'][0]['performed']
        if is_performed:
            assert not any((type_slug, test_source_id, configuration_parameters)), \
                f'configuration {str(id)} has already been performed, only name is editable'

        if name:
            name = validators.validate_text(name)

        if type_slug:
            assert type_slug in const.TESTTYPE_CHOICE, \
                f'invalid choice of type_slug (valid choices: {const.TESTTYPE_CHOICE})'
        else:
            type_slug = original['configuration'][0]['type_slug']

        repo_query = {
            'type_slug': type_slug,
            'confId': str(id),
            'confName': name or '',
            'userId': user_id,
            'sourceId': str(test_source_id) or "",
            'fetchSource': bool(test_source_id),
        }

        repo = gclient.execute(gql('''query ($confId:uuid!, $confName:String, $sourceId:uuid!, $fetchSource:Boolean!, $userId:uuid!, $type_slug:String!) {
            test_source (where:{
                    id:{_eq:$sourceId}, 
                    project:{userProjects:{user_id:{_eq:$userId}}}
            }) @include(if:$fetchSource) {
                source_type
                project {
                    userProjects { user_id }
                }
                repository {
                    name
                    url
                    configuration_type { slug_name }
                    project {
                        userProjects { user_id }
                    }
                }
                test_creator {
                    name
                    data
                    min_wait
                    max_wait
                    project {
                        userProjects { user_id }
                    }
                }
            }
            
            parameter (where:{configuration_type:{slug_name:{_eq:$type_slug}}}) {
                id
                default_value
                param_name
                name
                slug_name
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

        if name and name != original['configuration'][0]['name']:
            name = validators.validate_text(name)
            assert len(repo.get('isNameUnique', [])) == 0, f'configuration named "{name}" already exists'
            query_data['name'] = name

        if type_slug:
            query_data['type_slug'] = type_slug

        if test_source_id:
            test_source = repo.get('test_source')
            assert len(test_source), f'test_source {str(test_source_id)} does not exist'
            test_source = test_source[0]

            if test_source['source_type'] == const.CONF_SOURCE_REPO:
                assert test_source.get('repository', None), f'repository does not exist'
                validators.validate_repository(user_id=user_id, repo_config=test_source['repository'])
                validators.validate_accessibility(current_app.config, test_source['repository']['url'])
                query_data['test_source_id'] = str(test_source_id)
            elif test_source['source_type'] == const.CONF_SOURCE_JSON:
                assert test_source.get('test_creator', None), f'test_creator does not exist'
                validators.validate_test_creator(
                    test_source['test_creator']['data'],
                    min_wait=test_source['test_creator']['min_wait'],
                    max_wait=test_source['test_creator']['max_wait']
                )
                query_data['test_source_id'] = str(test_source_id)
            else:
                raise AssertionError(f'test source {str(test_source_id)} is invalid: {test_source["source_type"]}')

        if configuration_parameters:
            patched_params = validators.validate_test_params(configuration_parameters, defaults=repo['parameter'])
            if patched_params:
                query_data['configuration_parameters'] = {'data': []}
                for parameter_slug, param_value in patched_params.items():
                    query_data['configuration_parameters']['data'].append({
                        'parameter_slug': parameter_slug,
                        'value': param_value,
                    })
                    # calculate instances number based on num of users
                    if parameter_slug == const.TESTPARAM_USERS:
                        query_data['instances'] = math.ceil(int(param_value) / const.TESTRUN_MAX_USERS_PER_INSTANCE)

        return query_data

    def mutate(self, info, id, name=None, type_slug=None, test_source_id=None, configuration_parameters=None):
        UpdateValidate.validate(info, id, name, type_slug, test_source_id, configuration_parameters)
        return ValidationResponse(ok=True)


class Update(UpdateValidate):
    """Validates and saves configuration for a testrun."""

    Output = OutputTypeFactory(ConfigurationType, 'Update')

    def mutate(self, info, id, name=None, type_slug=None, test_source_id=None, configuration_parameters=None):
        gclient = hasura_client(current_app.config)

        query_params = UpdateValidate.validate(info, id, name, type_slug, test_source_id, configuration_parameters)

        conf_params = query_params.pop('configuration_parameters', None)
        if conf_params:
            for cp in conf_params['data']:
                gclient.execute(gql('''mutation ($confId:uuid!, $slug:String!, $value:String!) {
                    update_configuration_parameter(
                        where:{ configuration_id:{_eq:$confId}, parameter_slug:{_eq:$slug} },
                        _set:{ value: $value }
                    ) {
                        affected_rows
                    }
                }'''), variable_values={
                    'confId': str(id),
                    'slug': cp['parameter_slug'],
                    'value': cp['value']
                })

        query = gql('''mutation ($id:uuid!, $data:configuration_set_input!) {
            update_configuration(
                where:{id:{_eq:$id}},
                _set: $data
            ) {
                returning { id name type_slug project_id test_source_id } 
            }
        }''')

        conf_response = gclient.execute(query, variable_values={'id': str(id), 'data': query_params})
        assert conf_response['update_configuration'], f'cannot update configuration ({str(conf_response)})'

        return OutputValueFromFactory(Update, conf_response['update_configuration'])
