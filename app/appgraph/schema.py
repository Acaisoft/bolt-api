import graphene

from app.appgraph import configuration, testrun
from app.appgraph import oauth


class RootQuery(oauth.QueryOauth, testrun.TestrunQueries):
    pass


class RootMutations(graphene.ObjectType):
    testrun_configuration_create = configuration.CreateConfiguration.Field(name='testrun_configuration_create')
    testrun_start = testrun.TestrunStart.Field(name="testrun_start")


AppSchema = graphene.Schema(
    query=RootQuery,
    mutation=RootMutations,
    types=[
        configuration.Configuration,
        oauth.Oauth,
        oauth.OauthAuthtoken,
        testrun.TestrunStartObject,
        testrun.StatusResponse,
    ],
)
