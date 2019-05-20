import graphene
import math
from flask import current_app
from apps.bolt_api.app.appgraph.configuration import types
from services import const, gql_util
from services import validators
from services.hasura import hce


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
            types.ConfigurationParameterInput,
            required=False,
            description='Default parameter types overrides.')
        configuration_envvars = graphene.List(
            types.ConfigurationEnvVarInput,
            required=False,
            description='Parameters passed as environment variables to testrunner.')
        has_pre_test = graphene.Boolean(
            required=False,
            description='Test has pre_test hooks.')
        has_post_test = graphene.Boolean(
            required=False,
            description='Test has post_test hooks.')
        has_load_tests = graphene.Boolean(
            required=False,
            description='Test has load_tests hooks.')
        has_monitoring = graphene.Boolean(
            required=False,
            description='Test has monitoring hooks.')

    Output = gql_util.ValidationInterface

    @staticmethod
    def validate(
            info, name, type_slug, project_id,
            test_source_id=None, configuration_parameters=None, configuration_envvars=None,
            has_pre_test=False, has_post_test=False, has_load_tests=False, has_monitoring=False):
        project_id = str(project_id)

        assert type_slug in const.TESTTYPE_CHOICE, \
            f'invalid choice of type_slug (valid choices: {const.TESTTYPE_CHOICE})'

        name = validators.validate_text(name)

        role, user_id = gql_util.get_request_role_userid(
            info,
            (const.ROLE_ADMIN, const.ROLE_TENANT_ADMIN, const.ROLE_MANAGER, const.ROLE_TESTER)
        )

        assert any((has_pre_test, has_post_test, has_load_tests, has_monitoring)), \
            f'At least one section is required'

        repo_query = {
            'type_slug': type_slug,
            'confName': name,
            'projId': project_id,
            'userId': user_id,
            'sourceId': str(test_source_id) or "",
            'fetchSource': bool(test_source_id),
        }

        repo = hce(current_app.config, '''query (
                $confName:String, $sourceId:uuid!, $fetchSource:Boolean!, 
                $projId:uuid!, $userId:uuid!, $type_slug:String!
        ) {
            test_source (where:{
                    id:{_eq:$sourceId}, 
                    project:{
                        userProjects:{user_id:{_eq:$userId}}
                        is_deleted: {_eq:false}
                    }
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
                is_deleted: {_eq:false},
                name:{_eq:$confName}, 
                project_id:{_eq:$projId}, 
                project:{
                    userProjects:{user_id:{_eq:$userId}},
                    is_deleted: {_eq:false}
                }
            }) {
                id
            }
        }''', repo_query)

        if role not in (const.ROLE_ADMIN, const.ROLE_TENANT_ADMIN):
            assert repo.get('user_project', None), \
                f'non-admin ({role}) user {user_id} does not have access to project {project_id}'

        assert repo.get('project_by_pk', None), f'project "{project_id}" does not exist'

        assert len(repo.get('configuration', [])) == 0, f'configuration named "{name}" already exists'

        query_data = {
            'name': name,
            'project_id': project_id,
            'has_pre_test': has_pre_test,
            'has_post_test': has_post_test,
            'has_load_tests': has_load_tests,
            'has_monitoring': has_monitoring,
        }

        if user_id:
            query_data['created_by_id'] = user_id

        if type_slug:
            query_data['type_slug'] = type_slug

        if configuration_envvars:
            for rp in configuration_envvars:
                assert rp['name'].replace('_', '').isalnum(), \
                    f'configuration runner_parameter "{rp["name"]}" is not alphanumeric'
                assert not rp['name'].startswith('BOLT_'), f'environment variable cannot start with BOLT_'
            query_data['configuration_envvars'] = {
                'data': [{
                    'name': x['name'],
                    'value': x['value'],
                } for x in configuration_envvars]
            }

        if has_load_tests:
            patched_params = validators.validate_load_test_params(configuration_parameters or [], defaults=repo['parameter'])
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

        if has_monitoring:
            monitoring_parameters = validators.validate_monitoring_params(configuration_parameters or [], defaults=repo['parameter'])
            if monitoring_parameters:
                if 'configuration_parameters' not in query_data:
                    query_data['configuration_parameters'] = {'data': []}
                for slug, value in monitoring_parameters.items():
                    query_data['configuration_parameters']['data'].append({
                        'parameter_slug': slug,
                        'value': value,
                    })

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

    def mutate(
            self, info, name, type_slug, project_id, test_source_id=None, configuration_parameters=None,
            configuration_envvars=None, has_pre_test=False, has_post_test=False, has_load_tests=False,
            has_monitoring=False):
        CreateValidate.validate(
            info, name, type_slug, project_id, test_source_id, configuration_parameters,
            configuration_envvars, has_pre_test, has_post_test, has_load_tests, has_monitoring
        )
        return gql_util.ValidationResponse(ok=True)


class Create(CreateValidate):
    """Validates and saves configuration for a testrun."""

    Output = gql_util.OutputTypeFactory(types.ConfigurationType, 'Create')

    def mutate(
            self, info, name, type_slug, project_id, test_source_id=None, configuration_parameters=None,
            configuration_envvars=None, has_pre_test=False, has_post_test=False, has_load_tests=False, has_monitoring=False):
        query_params = CreateValidate.validate(
            info, name, type_slug, project_id, test_source_id, configuration_parameters, configuration_envvars,
            has_pre_test, has_post_test, has_load_tests, has_monitoring
        )

        query = '''mutation ($data:[configuration_insert_input!]!) {
            insert_configuration(
                objects: $data
            ) {
                returning { 
                    id 
                    name 
                    type_slug 
                    project_id 
                    test_source_id
                    has_pre_test
                    has_post_test
                    has_load_tests
                    has_monitoring
                    configuration_parameters {
                        parameter_slug
                        value
                    }
                    configuration_envvars {
                        name
                        value
                    }
                } 
            }
        }'''

        conf_response = hce(current_app.config, query, variable_values={'data': query_params})
        assert conf_response['insert_configuration'], f'cannot save configuration ({str(conf_response)})'

        return gql_util.OutputValueFromFactory(Create, conf_response['insert_configuration'])
