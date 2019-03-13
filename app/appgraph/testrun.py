import json
from datetime import datetime

import graphene
from flask import current_app
from gql import gql

from app import const
from app.appgraph.util import get_request_role_userid
from app.deployer import clients
from app.deployer.utils import start_job, get_test_run_status
from app.validators.configuration import validate_test_configuration_by_id
from bolt_api.upstream.devclient import devclient
from bolt_api.upstream import execution


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
        role, user_id = get_request_role_userid(info)

        assert role in (
            const.ROLE_ADMIN, const.ROLE_MANAGER), f'only managers and admins may start a test run (you are {role})'

        validate_test_configuration_by_id(str(conf_id))

        gclient = devclient(current_app.config)
        if role == const.ROLE_ADMIN:
            test_config_response = gclient.execute(gql('''query ($confId:uuid!) {
                configuration (where:{id:{_eq:$confId}}) {
                    project_id
                    repository {
                        url
                    }
                }
            }'''), {'confId': str(conf_id)})
        else:
            test_config_response = gclient.execute(gql('''query ($confId:uuid!, $userId:uuid!) {
                configuration (where:{
                id:{_eq:$confId},
                project:{userProjects:{user_id:{_eq:$userId}}}
                }) {
                    project_id
                    repository {
                        url
                    }
                }
            }'''), {
                'confId': str(conf_id),
                'userId': user_id,
            })
        assert test_config_response['configuration'], f'configuration not found ({str(test_config_response)})'
        test_config = test_config_response['configuration'][0]

        exec_result = gclient.execute(gql('''mutation ($data:[execution_insert_input!]!) {
        insert_execution(objects:$data) 
            {returning {id}}
        }'''), variable_values={'data': {
            'configuration_id': str(conf_id),
            'start': str(datetime.now()),
            'status': 'INIT',
        }})
        assert exec_result['insert_execution'], f'execution creation failed ({str(exec_result)}'

        execution_id = exec_result['insert_execution']['returning'][0]['id']

        deployer_response = start_job(
            app_config=current_app.config,
            project_id=test_config['project_id'],
            repo_url=test_config['repository']['url'],
            execution_id=execution_id,
            no_cache_redis=no_cache or no_cache_redis,
            no_cache_kaniko=no_cache or no_cache_kaniko,
        )

        query_vars = {
            'execId': execution_id,
            'data': {
                'status': const.TESTRUN_PREPARING,
                'test_preparation_job_id': deployer_response.id,
                'test_preparation_job_status': deployer_response.status,
            }}
        resp = gclient.execute(gql('''mutation ($execId:UUID!, $data:execution_set_input!) {
            update_execution(where:{id:{_eq: $execId}}, _set: $data) {returning {id} }
        }'''), variable_values=query_vars)
        assert resp['update_execution'], f'error updating execution state: {str(resp)}'

        return TestrunStartObject(execution_id=execution_id)


class StatusResponseInterface(graphene.Interface):
    status = graphene.String()
    debug = graphene.String()


class StatusResponse(graphene.ObjectType):
    class Meta:
        description = ''
        interfaces = (StatusResponseInterface,)


class TestrunQueries(graphene.ObjectType):
    testrun_status = graphene.Field(
        StatusResponseInterface,
        name='testrun_status',
        description='Check tests status, requires connection to bolt-deployer. Writes error details to execution table.',
        execution_id=graphene.UUID(description='Execution to check status of.')
    )

    testrun_repository_key = graphene.String(
        name='testrun_repository_key',
        description='Returns id rsa public key. Use it to give Bolt access to repository containing tests.'
    )

    def resolve_testrun_status(self, info, execution_id):
        status, debug = get_test_run_status(str(execution_id))
        return StatusResponse(status=status, debug=debug)

    def resolve_testrun_repository_key(self, info, **kwargs):
        response = clients.management(current_app.config).management_id_rsa_pub_get()
        return response.id_rsa_pub