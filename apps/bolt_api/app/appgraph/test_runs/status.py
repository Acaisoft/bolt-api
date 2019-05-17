import graphene
from flask import current_app

from services.deployer import clients
from services.testruns.status import get_test_run_status


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
