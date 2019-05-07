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
            required=True,
            description='Default parameter types overrides.')
        runner_parameters = graphene.List(
            types.ConfigurationParameterInput,
            required=False,
            description='Parameters passed as environment variables to testrunner.')

    Output = gql_util.ValidationInterface

    @staticmethod
    def validate(info, name, type_slug, project_id, test_source_id=None, configuration_parameters=None, runner_parameters=None):
        project_id = str(project_id)

        assert type_slug in const.TESTTYPE_CHOICE, f'invalid choice of type_slug (valid choices: {const.TESTTYPE_CHOICE})'

        name = validators.validate_text(name)

        role, user_id = gql_util.get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_MANAGER, const.ROLE_TESTER))

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

        if runner_parameters:
            for rp in runner_parameters:
                assert rp['parameter_slug'].replace('_', '').isalnum(), \
                    f'configuration runner_parameter "{rp["parameter_slug"]}" is not alphanumeric'
                assert not rp['parameter_slug'].startswith('BOLT_'), f'runner_parameter cannot start with BOLT_'
            query_data['configuration_envvars'] = {
                'data': [{
                    'name': x['parameter_slug'],
                    'value': x['value'],
                } for x in runner_parameters]
            }

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

    def mutate(self, info, name, type_slug, project_id, test_source_id=None, configuration_parameters=None, runner_parameters=None):
        CreateValidate.validate(info, name, type_slug, project_id, test_source_id, configuration_parameters, runner_parameters)
        return gql_util.ValidationResponse(ok=True)


class Create(CreateValidate):
    """Validates and saves configuration for a testrun."""

    Output = gql_util.OutputTypeFactory(types.ConfigurationType, 'Create')

    def mutate(self, info, name, type_slug, project_id, test_source_id=None, configuration_parameters=None, runner_parameters=None):

        query_params = CreateValidate.validate(info, name, type_slug, project_id, test_source_id, configuration_parameters, runner_parameters)

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
                    configuration_parameters {
                        parameter_slug
                        value
                    }
                    runner_parameters:configuration_envvars {
                        parameter_slug:name
                        value
                    }
                } 
            }
        }'''

        conf_response = hce(current_app.config, query, variable_values={'data': query_params})
        assert conf_response['insert_configuration'], f'cannot save configuration ({str(conf_response)})'

        return gql_util.OutputValueFromFactory(Create, conf_response['insert_configuration'])
