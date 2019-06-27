import graphene
from flask import current_app

from services import const, gql_util
from services.projects.summary import get_project_summary


class SummaryItem(graphene.ObjectType):
    project_id = graphene.String()
    description = graphene.String()
    image_url = graphene.String()
    name = graphene.String()
    num_scenarios = graphene.Int()
    num_sources = graphene.Int()
    num_tests_passed = graphene.Int()
    num_tests_failed = graphene.Int()
    invitation_open = graphene.Boolean()


class SummaryResponse(graphene.ObjectType):
    projects = graphene.List(SummaryItem)


class TestrunQueries(graphene.ObjectType):

    testrun_project_summary = graphene.Field(
        SummaryResponse,
        description='Summary of all projects.',
    )

    def resolve_testrun_project_summary(self, info):
        role, user_id = gql_util.get_request_role_userid(info, const.ROLE_CHOICE)

        stats = get_project_summary(current_app.config, user_id, role)

        out = [SummaryItem(**i) for i in stats]

        return SummaryResponse(projects=out)
