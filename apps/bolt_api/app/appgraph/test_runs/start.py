from datetime import datetime

import graphene
from flask import current_app

from services import const, gql_util
from services.deployer.utils import start_job, start_image
from services.validators.configuration import validate_test_configuration_by_id
from services.hasura import hce


class TestrunStartInterface(graphene.Interface):
    """Holds testrun_start response."""
    execution_id = graphene.UUID(description='id of started execution')


class TestrunStartObject(graphene.ObjectType):
    class Meta:
        interfaces = (TestrunStartInterface,)


class TestrunStart(graphene.Mutation):
    """Starts tests for given configuration. Returns id of "execution" entry to track tests progress.
    Call testrun_status to check on job progress.
    """
    class Arguments:
        conf_id = graphene.UUID(required=True, description='configuration to start tests for')
        no_cache = graphene.Boolean(required=False, description='ignore both caches')
        no_cache_redis = graphene.Boolean(required=False, description='ignore redis cache')
        no_cache_kaniko = graphene.Boolean(required=False, description='ignore redis kaniko')

    Output = TestrunStartInterface

    def mutate(self, info, conf_id, no_cache=False, no_cache_redis=False, no_cache_kaniko=False, **kwargs):
        role, user_id = gql_util.get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_MANAGER, const.ROLE_TESTER))

        validate_test_configuration_by_id(str(conf_id))

        test_config_response = hce(current_app.config, '''query ($confId:uuid!, $userId:uuid!) {
            configuration (where:{
                id:{_eq:$confId},
                project:{
                    userProjects:{user_id:{_eq:$userId}}
                    is_deleted: {_eq:false}
                }
            }) {
                project_id
                instances
                
                test_source {
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
            }
        }''', {
            'confId': str(conf_id),
            'userId': user_id,
        })
        assert test_config_response['configuration'], f'configuration not found ({str(test_config_response)})'
        test_config = test_config_response['configuration'][0]
        code_source = test_config['test_source']['source_type']

        initial_state = {
            'configuration_id': str(conf_id),
            'start': str(datetime.now()),
            'status': const.TESTRUN_PREPARING,
        }

        if code_source == const.CONF_SOURCE_REPO:
            deployer_response, execution_id = start_job(
                app_config=current_app.config,
                project_id=test_config['project_id'],
                workers=test_config['instances'],
                repo_url=test_config['test_source']['repository']['url'],
                no_cache_redis=no_cache or no_cache_redis,
                no_cache_kaniko=no_cache or no_cache_kaniko,
            )
            initial_state['test_preparation_job_id'] = deployer_response.id
            initial_state['test_preparation_job_status'] = deployer_response.status
        elif code_source == const.CONF_SOURCE_JSON:
            deployer_response, execution_id = start_image(
                app_config=current_app.config,
                project_id=test_config['project_id'],
                workers=test_config['instances'],
            )
            initial_state['status'] = const.TESTRUN_STARTED
            initial_state['test_job_id'] = deployer_response.name
            initial_state['test_preparation_job_status'] = str(deployer_response.status)
        else:
            raise Exception(f'invalid code source value {code_source}')

        initial_state['id'] = str(execution_id)

        exec_result = hce(current_app.config, '''mutation ($data:[execution_insert_input!]!) {
        insert_execution(objects:$data) 
            {returning {id}}
        }''', variable_values={'data': initial_state})
        assert exec_result['insert_execution'], f'execution creation failed ({str(exec_result)}'

        return TestrunStartObject(execution_id=execution_id)
