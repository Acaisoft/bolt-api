from datetime import datetime

import deployer_cli
from deployer_cli.rest import ApiException
from flask import current_app
from gql import gql

from app import const
from app.const import TENANT_ID
from app.deployer import clients
from bolt_api.upstream.devclient import devclient


def start_job(app_config, project_id, repo_url, execution_id) -> deployer_cli.ImageBuildTaskSchema:
    data = deployer_cli.ImageBuildRequestSchema(
        repo_url=repo_url,
        tenant_id=TENANT_ID,
        project_id=project_id,
        start_proper_job=True,
        test_run_execution_id=execution_id,
    )
    return clients.images(app_config).image_builds_post(image_build_request_schema=data)


def get_test_run_status(execution_id:str):
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
    exec_response = devclient(current_app.config).execute(gql('''query ($exec_id:uuid!) {
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
            return get_test_preparation_job_status(execution_id, str(execution['test_preparation_job_id']))
        else:
            return execution['test_preparation_job_status']
    elif execution['status'] in (const.TESTRUN_PREPARING_FAILED, const.TESTRUN_FINISHED):
        return execution['status']
    else:
        return get_test_job_status(execution['test_job_id'])


def can_refresh_test_preparation_job_status():
    # TODO
    return True


def get_test_preparation_job_status(execution_id:str, test_preparation_job_id:str):
    response = clients.images(current_app.config).image_builds_task_id_get(task_id=test_preparation_job_id)

    err = None
    test_job_id = None
    new_status = const.TESTRUN_PREPARING

    if response.status == 'FAILURE':
        new_status = const.TESTRUN_PREPARING_FAILED
        if response.state and response.state['error']:
            err = response.state['error']

    if response.status == 'SUCCESS':
        new_status = const.TESTRUN_STARTED
        test_job_id = response.state['result']['job_name']

    update_data = {
        'exec_id': execution_id,
        'test_job_id': test_job_id,
        'status': new_status,
        'jobError': err,
        'jobStatus': response.status,
        'checkTime': str(datetime.now()),
    }

    update_response = devclient(current_app.config).execute(gql('''mutation ($exec_id:uuid!, $test_job_id:String, $status:String!, $jobError:String, $jobStatus:String, $checkTime:timestamptz!) {
        update_execution(_set:{
            status: $status,
            test_job_id: $test_job_id,
            test_preparation_job_error: $jobError,
            test_preparation_job_status: $jobStatus,
            test_preparation_job_statuscheck_timestamp: $checkTime,
        }, where:{id:{_eq:$exec_id}}) { returning { id } }
    }'''), update_data)

    return response.status


def get_test_job_status(test_job_id):
    try:
        return clients.jobs(current_app.config).jobs_job_id_get(job_id=test_job_id)
    except ApiException as e:
        if e.status == 404:
            raise Exception('job not found, is the id valid?')
        else:
            raise e
