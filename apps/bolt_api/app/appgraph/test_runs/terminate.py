import graphene
import requests

from flask import current_app

from services import const, gql_util
from services.hasura import hce
from services.logger import setup_custom_logger

logger = setup_custom_logger(__file__)


class TestrunTerminateInterface(graphene.Interface):
    message = graphene.String(description='message with text status')
    ok = graphene.Boolean(description='boolean status true | false')


class TestrunTerminateObject(graphene.ObjectType):
    class Meta:
        interfaces = (TestrunTerminateInterface,)


class TestrunTerminate(graphene.Mutation):
    class Arguments:
        argo_name = graphene.String(required=True)

    Output = TestrunTerminateInterface

    @staticmethod
    def terminate_flow(argo_name):
        endpoint = current_app.config['WORKFLOW_TERMINATE_ENDPOINT']
        response = requests.post(endpoint, json={'workflow_name': argo_name})
        if response.status_code == 200:
            logger.info(f'Workflow {argo_name} was successfully terminated. Response: {response.json()}')
            return True, '200. Workflow was successfully terminated'
        else:
            logger.info(f'Error during terminating workflow | {response.status_code} | {response.text}')
            return False, f'{response.status_code}. Error during terminating workflow'

    @staticmethod
    def update_execution_status(argo_name):
        query = '''
            mutation ($argo_name: String, $status: String) {
                update_execution(where: {argo_name: {_eq: $argo_name}}, _set: {status: $status}) {
                    affected_rows
                }
            }
        '''
        response = hce(current_app.config, query, {'argo_name': argo_name, 'status': 'TERMINATED'})
        try:
            rows_updated = response['update_execution']['affected_rows']
            logger.info(f'Updated rows during terminating: {rows_updated}')
            return True if rows_updated == 1 else False
        except KeyError:
            logger.exception(f'Error during updating execution status (TERMINATE)')
            return False

    def mutate(self, info, argo_name):
        role, user_id = gql_util.get_request_role_userid(
            info, (const.ROLE_ADMIN, const.ROLE_TENANT_ADMIN, const.ROLE_MANAGER, const.ROLE_TESTER))
        logger.info(f'Executed mutation `testrun_terminate` | {argo_name} | {role} | {user_id}')
        # try to terminate flow
        ok, message = TestrunTerminate.terminate_flow(argo_name)
        if ok:
            # try to update execution status by argo_name
            updated_successfully = TestrunTerminate.update_execution_status(argo_name)
            if not updated_successfully:
                ok, message = False, 'Error during updating status for execution'
        # return response with statuses
        out = TestrunTerminateObject(message=message, ok=ok)
        return out
