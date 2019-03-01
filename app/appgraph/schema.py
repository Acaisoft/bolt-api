import graphene

from app.appgraph import configuration, testrun
from app.appgraph import oauth


class TestrunQuery(oauth.QueryOauth, testrun.TestrunQueries):
    pass


class TestrunMutations(graphene.ObjectType):
    testrun_configuration_create = configuration.CreateConfiguration.Field(
        name='testrun_configuration_create',
        description=configuration.CreateConfiguration.__doc__
    )
    testrun_start = testrun.TestrunStart.Field(
        name="testrun_start",
        description=testrun.TestrunStart.__doc__
    )


AppSchema = graphene.Schema(
    query=TestrunQuery,
    mutation=TestrunMutations,
    types=[
        configuration.Configuration,
        oauth.Oauth,
        oauth.OauthAuthtoken,
        testrun.TestrunStartObject,
        testrun.StatusResponse,
    ],
)
