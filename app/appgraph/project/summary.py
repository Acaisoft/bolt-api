import graphene
from flask import current_app

from app import const
from app.appgraph.util import get_request_role_userid
from app.services.hasura.hasura_client import hce
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
        _, user_id = get_request_role_userid(info, const.ROLE_CHOICE)

        projects = hce(current_app.config, '''query ($pid:uuid!, $uid:uuid!) {
            user_project(where:{user_id:{_eq:$uid}, project_id:{_eq:$pid}}) {
            id
            }
        }''', {'pid': str(project_id), 'uid': user_id})
        assert projects['user_project'], f'unauthorized request'

        stats = get_project_summary(current_app.config, project_id)

        return SummaryResponse(**stats)
