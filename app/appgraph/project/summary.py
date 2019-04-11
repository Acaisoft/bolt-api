import graphene
from flask import current_app

from app import const
from app.appgraph.util import get_request_role_userid
from app.services.projects.summary import get_project_summary


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
        description='Check tests status, requires connection to bolt-deployer. Writes error details to execution table.',
        project_id=graphene.UUID(description='Project id.')
    )

    def resolve_testrun_project_summary(self, info, project_id):
        role, user_id = get_request_role_userid(info, const.ROLE_CHOICE)

        # TODO: check user role

        stats = get_project_summary(current_app.config, project_id)

        return SummaryResponse(**stats)
