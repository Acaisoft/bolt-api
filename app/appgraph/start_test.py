from datetime import datetime

import graphene
from flask import current_app
from gql import gql

from app.deployer.clients import start_job
from bolt_api.upstream.devclient import devclient
from bolt_api.upstream import execution


class StartTestInterface(graphene.Interface):
    execution_id = graphene.UUID()


class StartTest(graphene.ObjectType):
    class Meta:
        interfaces = (StartTestInterface,)


class StartTestRun(graphene.Mutation):
    class Arguments:
        conf_id = graphene.UUID(required=True)

    Output = StartTestInterface

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

        return StartTest(execution_id=exec_result[0]['id'])


def validate_test_configuration(test_conf_id):
    # TODO:
    return
