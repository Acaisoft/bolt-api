import json
import deployer_cli
import requests

from services import const
from services.hasura.hasura import hasura_token_for_testrunner
from services.deployer import clients
from services.hasura import hce
from services.logger import setup_custom_logger
from services.testruns.defaults import DEPLOYER_TIMEOUT, DEFAULT_CHART_CONFIGURATION, NFS_CHART_CONFIGURATION
from services.validators import validate_extensions
from services.validators.configuration import validate_test_configuration_by_id, validate_monitoring_params

logger = setup_custom_logger(__file__)


def start_image(app_config, project_id, workers, extensions, run_monitoring, run_load_test, monitoring_deadline_secs):
    # request a testrun is started with parameters in execution's configuration
    image = app_config.get('BOLT_TEST_RUNNER_IMAGE', const.DEFAULT_TEST_RUNNER_IMAGE)
    assert image, '*_TEST_RUNNER_IMAGE is undefined'

    job_token, execution_id = hasura_token_for_testrunner(app_config)

    data = deployer_cli.JobCreateSchema(
        docker_image=image,
        workers=workers,
        tenant_id=const.TENANT_ID,
        project_id=project_id,
        test_run_execution_id=execution_id,
        job_auth_token=str(job_token),
        extensions=extensions,
        run_monitoring=run_monitoring,
        monitoring_deadline_secs=monitoring_deadline_secs,
        run_load_test=run_load_test,
    )

    try:
        return clients.jobs(app_config).jobs_post(
            job_create_schema=data,
            _request_timeout=DEPLOYER_TIMEOUT
        ), execution_id, job_token
    except Exception as e:
        if 'NewConnectionError' in str(e):
            logger.warn(str(e))
            raise AssertionError('Deployment Management service is temporarily overloaded, please try again later')
        else:
            raise


def start_job(app_config, project_id, repo_url, workers, no_cache, extensions, run_monitoring, run_load_test,
              monitoring_deadline_secs):
    # request an image is built from repository sources and executed as testrun

    job_token, execution_id = hasura_token_for_testrunner(app_config)

    data = deployer_cli.ImageBuildRequestSchema(
        repo_url=repo_url,
        workers=workers,
        tenant_id=const.TENANT_ID,
        project_id=project_id,
        start_proper_job=True,
        test_run_execution_id=execution_id,
        job_auth_token=str(job_token),
        no_cache=no_cache,
        no_cache_kaniko=no_cache,
        extensions=extensions,
        run_monitoring=run_monitoring,
        monitoring_deadline_secs=monitoring_deadline_secs,
        run_load_test=run_load_test,
    )

    try:
        return clients.images(app_config).image_builds_post(
            image_build_request_schema=data,
            _request_timeout=DEPLOYER_TIMEOUT
        ), execution_id, job_token
    except Exception as e:
        if 'NewConnectionError' in str(e):
            logger.warn(str(e))
            raise AssertionError('Image Build service is temporarily overloaded, please try again later')
        else:
            raise


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
            }

            configuration_extensions {
                type
                extension_params {
                    name
                    value
                }
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

    test_extensions = validate_extensions(test_config['configuration_extensions'])
    monitoring_deadline_secs = 0
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
        workflow_data = {
            'tenant_id': '1',
            'project_id': test_config['project_id'],
            'repository_url': test_config['test_source']['repository']['url'],
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
        if test_config['has_load_tests']:
            workflow_data['job_load_tests'] = {'env_vars': {}, 'workers': test_config['instances']}
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
        deployer_response, execution_id, hasura_token = start_image(
            app_config=app_config,
            project_id=test_config['project_id'],
            workers=test_config['instances'],
            extensions=test_extensions,
            monitoring_deadline_secs=monitoring_deadline_secs,
            run_monitoring=test_config['has_monitoring'],
            run_load_test=test_config['has_load_tests'],
        )
        initial_state['status'] = const.TESTRUN_STARTED
        initial_state['test_job_id'] = deployer_response.name
        initial_state['test_preparation_job_status'] = str(deployer_response.status)
    else:
        raise Exception(f'invalid code source value {code_source}')

    initial_state['id'] = str(execution_id)

    exec_result = hce(app_config, '''mutation ($data:[execution_insert_input!]!) {
    insert_execution(objects:$data) 
        {returning {id}}
    }''', variable_values={'data': initial_state})
    assert exec_result['insert_execution'], f'execution creation failed ({str(exec_result)}'

    return str(execution_id), hasura_token
