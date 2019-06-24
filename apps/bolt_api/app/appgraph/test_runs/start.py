import os

import graphene
from flask import current_app

from services import const, gql_util, testruns


class TestrunStartInterface(graphene.Interface):
    """Holds testrun_start response."""
    execution_id = graphene.UUID(description='id of started execution')
    hasura_token = graphene.String(description='jon auth token')


class TestrunStartObject(graphene.ObjectType):
    class Meta:
        interfaces = (TestrunStartInterface,)


class TestrunStart(graphene.Mutation):
    """Starts tests for given configuration. Returns id of "execution" entry to track tests progress.
    Call testrun_status to check on job progress.
    """
    class Arguments:
        conf_id = graphene.UUID(required=True, description='configuration to start tests for')
        no_cache = graphene.Boolean(required=False, description='ignore caches')
        debug = graphene.Boolean(required=False, description='use debugging tokens')

    Output = TestrunStartInterface

    def mutate(self, info, conf_id, no_cache=False, debug=False):
        role, user_id = gql_util.get_request_role_userid(
            info, (const.ROLE_ADMIN, const.ROLE_TENANT_ADMIN, const.ROLE_MANAGER, const.ROLE_TESTER))

        if debug and role == const.ROLE_ADMIN:
            os.environ['SELFSIGNED_TOKEN_FOR_TESTRUNNER'] = "1"

        execution_id, hasura_token = testruns.start(current_app.config, str(conf_id), user_id, no_cache)

        out = TestrunStartObject(execution_id=execution_id)

        if debug and role == const.ROLE_ADMIN:
            os.unsetenv('SELFSIGNED_TOKEN_FOR_TESTRUNNER')

        if role == const.ROLE_ADMIN:
            out.hasura_token = hasura_token

        return out
