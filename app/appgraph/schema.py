import graphene

from app.appgraph import configuration, testrun, util, project
from app.appgraph import oauth


class TestrunQuery(oauth.QueryOauth, testrun.TestrunQueries):
    pass


def to_field(gqlClass):
    return gqlClass.Field(description=gqlClass.__doc__)


class TestrunMutations(graphene.ObjectType):
    testrun_configuration_create = to_field(configuration.Create)
    testrun_configuration_validate = to_field(configuration.Validate)
    testrun_project_create = to_field(project.Create)
    testrun_project_validate = to_field(project.Validate)
    testrun_start = to_field(testrun.TestrunStart)


AppSchema = graphene.Schema(
    query=TestrunQuery,
    mutation=TestrunMutations,
    types=[
        configuration.ConfigurationType,
        project.ProjectType,
        oauth.Oauth,
        oauth.OauthAuthtoken,
        testrun.TestrunStartObject,
        testrun.StatusResponse,
        util.ValidationResponse,
    ],
    auto_camelcase=False,
)
