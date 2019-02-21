from datetime import datetime

import graphene
from flask import current_app
from gql import gql

from app.deployer import clients
from app.deployer.utils import start_job
from app.validators.configuration import validate_test_configuration
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
        validate_test_configuration(conf_id)

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

        deployer_response = start_job(
            app_config=current_app.config,
            project_id=test_config['project_id'],
            repo_url=test_config['repository']['url'],
            test_config_id=str(conf_id),
        )
        assert deployer_response.status == 'PENDING', f'unexpected bolt-deployer job status {deployer_response.status}'

        exec_result = execution.Query(gclient).insert(execution.Exec(
            configuration_id=str(conf_id),
            start=datetime.now(),
            status=deployer_response.status,
            test_preparation_job_id=deployer_response.id,
        ))

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
        exec_response = devclient(current_app.config).execute(gql('''query ($exec_id:uuid!) {
            execution (where:{id:{_eq:$exec_id}}) {
                test_preparation_job_id
            }
        }'''), {'exec_id': str(execution_id)})
        response = clients.jobs(current_app.config).jobs_job_id_get(
            job_id=exec_response['execution'][0]['test_preparation_job_id'])
        return StatusResponse(status=response.status)

    def resolve_testrun_repository_key(self, info, **kwargs):
        response = clients.management(current_app.config).management_id_rsa_pub_get()
        return response.id_rsa_pub
