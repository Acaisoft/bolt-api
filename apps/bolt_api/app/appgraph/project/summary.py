import graphene
from flask import current_app

from services import const, gql_util
from services.hasura.hasura_client import hce
from services.projects.summary import get_project_summary


class SummaryInterface(graphene.Interface):
    num_scenarios = graphene.Int()
    num_sources = graphene.Int()
    num_tests_passed = graphene.Int()
    num_tests_failed = graphene.Int()


class SummaryResponse(graphene.ObjectType):
    class Meta:
        interfaces = (SummaryInterface,)


class TestrunQueries(graphene.ObjectType):

    testrun_project_summary = graphene.Field(
        SummaryInterface,
        description='Summary of all projects.',
    )

    def resolve_testrun_project_summary(self, info):
        _, user_id = gql_util.get_request_role_userid(info, const.ROLE_CHOICE)

        stats = get_project_summary(current_app.config, user_id)

        return SummaryResponse(**stats)
