import subprocess
import graphene

from services import const, gql_util
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
        try:
            result = subprocess.check_output(['argo', '-n', 'argo', 'terminate', argo_name])
        except subprocess.CalledProcessError as ex:
            logger.exception(f'Exception during terminating argo flow {ex}')
            return False, str(ex)
        else:
            logger.info(f'Returned result during terminating argo flow {result}')
            return True, str(result)

    def mutate(self, info, argo_name):
        role, user_id = gql_util.get_request_role_userid(
            info, (const.ROLE_ADMIN, const.ROLE_TENANT_ADMIN, const.ROLE_MANAGER, const.ROLE_TESTER))
        logger.info(f'Executed mutation `testrun_terminate` | {argo_name} | {role} | {user_id}')
        status, message = TestrunTerminate.terminate_flow(argo_name)
        out = TestrunTerminateObject(message=message, ok=status)
        return out
