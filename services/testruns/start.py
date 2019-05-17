import deployer_cli
from datetime import datetime

from services import const
from services.hasura.hasura import hasura_token_for_testrunner
from services.deployer import clients
from services.hasura import hce
from services.validators import validate_extensions
from services.validators.configuration import validate_test_configuration_by_id

DEPLOYER_TIMEOUT = 10


def start_image(app_config, project_id, workers, extensions, run_monitoring, run_load_test):
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
        run_load_test=run_load_test,
    )
    return clients.jobs(app_config).jobs_post(
        job_create_schema=data,
        _request_timeout=DEPLOYER_TIMEOUT
    ), execution_id, job_token


def start_job(app_config, project_id, repo_url, workers, no_cache, extensions, run_monitoring, run_load_test):
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
        run_load_test=run_load_test,
    )
    return clients.images(app_config).image_builds_post(
        image_build_request_schema=data,
        _request_timeout=DEPLOYER_TIMEOUT
    ), execution_id, job_token


def start(app_config, conf_id, user_id, no_cache):
    validate_test_configuration_by_id(str(conf_id))

    test_config_response = hce(app_config, '''query ($confId:uuid!, $userId:uuid!) {
        configuration (where:{
            id:{_eq:$confId},
            project:{
                userProjects:{user_id:{_eq:$userId}}
                is_deleted: {_eq:false}
            }
        }) {
            project_id
            instances
            has_load_tests
            has_monitoring

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

    initial_state = {
        'configuration_id': str(conf_id),
        'start': str(datetime.now()),
        'status': const.TESTRUN_PREPARING,
    }

    if code_source == const.CONF_SOURCE_REPO:
        deployer_response, execution_id, hasura_token = start_job(
            app_config=app_config,
            project_id=test_config['project_id'],
            workers=test_config['instances'],
            repo_url=test_config['test_source']['repository']['url'],
            no_cache=no_cache,
            extensions=test_extensions,
            run_monitoring=test_config['has_monitoring'],
            run_load_test=test_config['has_load_tests'],
        )
        # initial_state['test_preparation_job_id'] = deployer_response.id
        # initial_state['test_preparation_job_status'] = deployer_response.status
    elif code_source == const.CONF_SOURCE_JSON:
        deployer_response, execution_id, hasura_token = start_image(
            app_config=app_config,
            project_id=test_config['project_id'],
            workers=test_config['instances'],
            extensions=test_extensions,
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
