import json
import requests

from services import const
from services.hasura.hasura import hasura_token_for_testrunner
from services.hasura import hce
from services.logger import setup_custom_logger
from services.testruns.defaults import DEFAULT_CHART_CONFIGURATION, NFS_CHART_CONFIGURATION
from services.validators import validate_extensions
from services.validators.configuration import validate_test_configuration_by_id, validate_monitoring_params

logger = setup_custom_logger(__file__)


def start(app_config, conf_id, user_id, no_cache):
    validate_test_configuration_by_id(str(conf_id))
    test_config_response = hce(app_config, '''query ($confId:uuid!, $userId:uuid!) {
        parameter {
            id
            default_value
            param_name
            name
            slug_name
        }
        
        configuration (where:{
            id:{_eq:$confId},
            project:{
                userProjects:{user_id:{_eq:$userId}}
                is_deleted: {_eq:false}
            }
        }) {
            name
            project_id
            instances
            has_pre_test
            has_post_test
            has_load_tests
            has_monitoring
            monitoring_chart_configuration
            configuration_parameters {
                parameter_slug
                value
                parameter {
                    name
                }
            }
            configuration_extensions {
                type
                extension_params {
                    name
                    value
                }
            }
            configuration_envvars {
                name
                value
            }
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

    validate_extensions(test_config['configuration_extensions'])  # TODO: probably can be deleted
    if test_config['has_monitoring']:
        monitoring_params = validate_monitoring_params(test_config['configuration_parameters'],
                                                       test_config_response['parameter'])
        monitoring_deadline_secs = monitoring_params.get('monitoring_duration', None)
        assert monitoring_deadline_secs is not None, \
            f'monitoring_duration/monitoring_deadline_secs must be a numeric value'

    # monitoring chart javascript configuration
    chart_config = test_config['monitoring_chart_configuration']
    if not chart_config:
        chart_config = json.loads(DEFAULT_CHART_CONFIGURATION)
    # override if NFS extension is defined
    exts = test_config['configuration_extensions']
    if len(exts) == 1 and exts[0]['type'] == const.EXTENSION_NFS:
        chart_config = json.loads(NFS_CHART_CONFIGURATION)

    initial_state = {
        'configuration_id': str(conf_id),
        'status': const.TESTRUN_PREPARING,
        'execution_metrics_metadata': {
            'data': {
                'chart_configuration': chart_config,
            },
        },
    }

    if code_source == const.CONF_SOURCE_REPO:
        hasura_token, execution_id = hasura_token_for_testrunner(app_config)
        # common workflow fields
        try:
            branch = [
                envvar['value'] for envvar in test_config['configuration_envvars'] if envvar['name'] == 'branch'
            ][0]
        except IndexError:
            branch = 'master'

        workflow_data = {
            'tenant_id': '1',
            'project_id': test_config['project_id'],
            'repository_url': test_config['test_source']['repository']['url'],
            'branch': branch,
            'execution_id': execution_id,
            'auth_token': hasura_token,
            'duration_seconds': 123,
            'job_pre_start': None,
            'job_load_tests': None,
            'job_monitoring': None,
            'job_post_stop': None,
            'no_cache': no_cache,
        }
        # pre start
        if test_config['has_pre_test']:
            workflow_data['job_pre_start'] = {'env_vars': {}}
        # load tests
        try:
            users = [
                parameter['value']
                for parameter in test_config['configuration_parameters']
                if parameter['parameter']['name'] == 'users'
            ][0]
        except IndexError:
            users = 0

        if test_config['has_load_tests']:
            workflow_data['job_load_tests'] = {
                'env_vars': {}, 'workers': test_config['instances'], 'users': users,
            }
        # monitoring
        if test_config['has_monitoring']:
            workflow_data['job_monitoring'] = {'env_vars': {}}
        # post stop
        if test_config['has_post_test']:
            workflow_data['job_post_stop'] = {'env_vars': {}}

        logger.info(f'Workflow creator data {workflow_data}')
        response = requests.post(app_config['WORKFLOW_CREATOR_ENDPOINT'], json=workflow_data)
        logger.info(f'Workflow response {response}')
        logger.info(f'Workflow response text {response.text} | Status {response.status_code}')
        assert response.status_code == 200, f'Error during execution workflow creator. Response {response.status_code}'
        try:
            json_response = response.json()
        except (json.decoder.JSONDecodeError, KeyError) as ex:
            logger.exception(f'Caught exception during getting json response from workflow creator | {ex}')
            assert False, f'Caught exception during getting json response from workflow creator | {ex}'
        else:
            # set argo_name for execution
            initial_state['argo_name'] = json_response['name']
            logger.info(f'Added argo_name field to initial_state data {initial_state}')
    elif code_source == const.CONF_SOURCE_JSON:
        # TODO: DEPRECATED. NEED TO FIX (merge to argo)
        deployer_response, execution_id, hasura_token = None, None, None
        initial_state['status'] = const.TESTRUN_PREPARING
    else:
        raise Exception(f'invalid code source value {code_source}')

    test_config.pop('monitoring_chart_configuration')  # delete monitoring chart from dict
    initial_state['id'] = str(execution_id)
    initial_state['configuration_snapshot'] = test_config
    exec_result = hce(app_config, '''mutation ($data:[execution_insert_input!]!) {
        insert_execution(objects:$data) 
            {returning {id}}
        }''', variable_values={'data': initial_state})
    assert exec_result['insert_execution'], f'execution creation failed ({str(exec_result)}'
    return str(execution_id), hasura_token
