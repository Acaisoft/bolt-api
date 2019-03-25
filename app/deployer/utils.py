import json
from datetime import datetime

import deployer_cli
from deployer_cli.rest import ApiException
from flask import current_app
from gql import gql

from app import const
from app.auth.hasura import hasura_token_for_testrunner
from app.const import TENANT_ID
from app.deployer import clients
from app.hasura_client import hasura_client


def start_job(app_config, project_id, repo_url, execution_id, no_cache_redis=False,
              no_cache_kaniko=False) -> deployer_cli.ImageBuildTaskSchema:
    job_token = hasura_token_for_testrunner(app_config, execution_id)
    data = deployer_cli.ImageBuildRequestSchema(
        repo_url=repo_url,
        tenant_id=TENANT_ID,
        project_id=project_id,
        start_proper_job=True,
        test_run_execution_id=execution_id,
        job_auth_token=job_token,
        no_cache=no_cache_redis,
        no_cache_kaniko=no_cache_kaniko,
    )
    return clients.images(app_config).image_builds_post(image_build_request_schema=data)


def get_test_run_status(execution_id: str):
    """
    Execution model stores the id and last known state of an image-build-job and testrun-job.
    To check current state of job:
    if status is const.TESTRUN_PREPARING:
        return/refresh test_preparation_job_status using test_preparation_job_id
    if status is const.TESTRUN_PREPARING_FAILED:
        return const.TESTRUN_PREPARING_FAILED
    if status is const.TESTRUN_STARTED:
        image was built succesfully, return/refresh test_job_id status

    :param execution_id:
    :return:
    """
    exec_response = hasura_client(current_app.config).execute(gql('''query ($exec_id:uuid!) {
        execution_by_pk (id:$exec_id) {
            status
            test_preparation_job_id
            test_preparation_job_error
            test_preparation_job_status
            test_preparation_job_statuscheck_timestamp
            test_job_id
        }
    }'''), {'exec_id': execution_id})

    assert exec_response['execution_by_pk'], f'invalid execution id: {str(exec_response)}'

    execution = exec_response['execution_by_pk']

    if execution['status'] == const.TESTRUN_PREPARING:
        if can_refresh_test_preparation_job_status():
            return get_test_preparation_job_status(execution_id, str(execution['test_preparation_job_id'])), execution
        else:
            return execution['test_preparation_job_status'], None
    elif execution['status'] in (const.TESTRUN_RUNNING, const.TESTRUN_STARTED, const.TESTRUN_CRASHED) and execution[
        'test_job_id']:
        # state was updated by test wrapper to TESTRUN_RUNNING but double-check with deployer jobs api
        # in case wrapper crashed
        return get_test_job_status(execution_id, execution['test_job_id'])

    return execution['status'], execution


def can_refresh_test_preparation_job_status():
    # TODO
    return True


def get_test_preparation_job_status(execution_id: str, test_preparation_job_id: str):
    response = clients.images(current_app.config).image_builds_task_id_get(task_id=test_preparation_job_id)

    err = None
    test_job_id = None
    commit_sha = None
    new_status = const.TESTRUN_PREPARING

    if response.status == 'FAILURE':
        new_status = const.TESTRUN_PREPARING_FAILED
        if response.state and response.state['error']:
            err = response.state['error']

    if response.status == 'SUCCESS':
        new_status = const.TESTRUN_STARTED
        test_job_id = response.state['result']['job_name']
        commit_sha = response.state.get('result', {}).get('commit_sha')

    update_data = {
        'exec_id': execution_id,
        'data': {
            'test_job_id': test_job_id,
            'status': new_status,
            'test_preparation_job_error': err,
            'test_preparation_job_status': response.status,
            'test_preparation_job_statuscheck_timestamp': str(datetime.now()),
        }
    }
    if commit_sha:
        update_data['data']['commit_hash'] = commit_sha

    update_response = hasura_client(current_app.config).execute(gql('''mutation ($exec_id:uuid!, $data:execution_insert_input!) {
        update_execution(_set: $data, where:{id:{_eq:$exec_id}}) { returning { id } }
    }'''), update_data)
    assert not update_response.get('error'), f'error updating execution: {str(update_response)}'

    return response.status


def get_test_job_status(execution_id: str, test_job_id: str):
    try:
        response_data = clients.jobs(current_app.config).jobs_job_id_get(job_id=test_job_id)
    except ApiException as e:
        if e.status == 404:
            raise Exception('job not found, is the id valid?')
        else:
            raise e

    err = None
    if not response_data.status.get('active'):
        if not response_data.status.get('succeeded'):
            status = const.TESTRUN_CRASHED
            err = response_data.status
        else:
            status = const.TESTRUN_FINISHED
    else:
        status = const.TESTRUN_RUNNING

    update_data = {
        'exec_id': execution_id,
        'data': {
            'status': status,
            'test_job_error': json.dumps(err),
            'test_preparation_job_statuscheck_timestamp': str(datetime.now()),
        },
    }

    update_response = hasura_client(current_app.config).execute(gql('''mutation ($exec_id:uuid!, $data:execution_insert_input!) {
        update_execution(_set:$data, where:{id:{_eq:$exec_id}}) { returning { id } }
    }'''), update_data)
    assert not update_response.get('error'), f'error updating execution: {str(update_response)}'

    return status, response_data
