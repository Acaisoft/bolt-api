from datetime import datetime

import graphene
from flask import current_app
from gql import gql

from app import const
from app.deployer import clients
from app.deployer.utils import start_job, get_test_run_status
from app.validators.configuration import validate_test_configuration_by_id
from bolt_api.upstream.devclient import devclient
from bolt_api.upstream import execution


class TestrunStartInterface(graphene.Interface):
    execution_id = graphene.UUID()


class TestrunStartObject(graphene.ObjectType):
    class Meta:
        interfaces = (TestrunStartInterface,)


class TestrunStart(graphene.Mutation):
    class Arguments:
        conf_id = graphene.UUID(required=True)

    Output = TestrunStartInterface

    def mutate(self, info, conf_id, **kwargs):
        validate_test_configuration_by_id(conf_id)

        gclient = devclient(current_app.config)
        test_config_response = gclient.execute(gql('''query ($conf_id:uuid!) {
            configuration (where:{id:{_eq:$conf_id}}) {
                project_id
                repository {
                    url
                }
            }
        }'''), {'conf_id': str(conf_id)})
        assert test_config_response['configuration'], f'configuration not found ({str(test_config_response)})'
        test_config = test_config_response['configuration'][0]

        exec_result = execution.Query(gclient).insert(execution.Exec(
            configuration_id=str(conf_id),
            start=datetime.now(),
            status='INIT',
        ))
        assert exec_result, f'execution creation failed ({str(exec_result)}'

        deployer_response = start_job(
            app_config=current_app.config,
            project_id=test_config['project_id'],
            repo_url=test_config['repository']['url'],
            execution_id=exec_result[0]['id'],
        )

        gclient.execute(gql('''mutation ($execId:UUID!, $state:String!, $jobId:String!, $jobState:String!) {
            update_execution(where:{id:{_eq: $execId}}, _set:{
                test_preparation_job_id: $jobId,
                status: $state,
                test_preparation_job_status: $jobState
            }) {affected_rows}
        }'''), {
            'execId': exec_result[0]['id'],
            'state': const.TESTRUN_PREPARING,
            'jobId': deployer_response.id,
            'jobState': deployer_response.status,
        })

        return TestrunStartObject(execution_id=exec_result[0]['id'])


class StatusResponseInterface(graphene.Interface):
    status = graphene.String()


class StatusResponse(graphene.ObjectType):
    class Meta:
        interfaces = (StatusResponseInterface,)


class TestrunQueries(graphene.ObjectType):
    testrun_status = graphene.Field(StatusResponseInterface, name='testrun_status', execution_id=graphene.UUID())

    testrun_repository_key = graphene.String(name='testrun_repository_key')

    def resolve_testrun_status(self, info, execution_id):
        status = get_test_run_status(str(execution_id))
        return StatusResponse(status=status)

    def resolve_testrun_repository_key(self, info, **kwargs):
        response = clients.management(current_app.config).management_id_rsa_pub_get()
        return response.id_rsa_pub
