import graphene

from app.appgraph import configuration, start_test
from app.appgraph import oauth


class RootQuery(configuration.QueryConfiguration, oauth.QueryOauth):
    pass


class RootMutations(graphene.ObjectType):
    create_configuration = configuration.CreateConfiguration.Field()
    start_test = start_test.StartTestRun.Field(name="start_test")


AppSchema = graphene.Schema(
    query=RootQuery,
    mutation=RootMutations,
    types=[configuration.Configuration, oauth.Oauth, oauth.OauthAuthtoken, start_test.StartTest],
)
