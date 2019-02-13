import graphene

from app.appgraph import configuration
from app.appgraph import oauth


class RootQuery(configuration.QueryConfiguration, oauth.QueryOauth):
    pass


class RootMutations(graphene.ObjectType):
    create_configuration = configuration.CreateConfiguration.Field()


AppSchema = graphene.Schema(
    query=RootQuery,
    mutation=RootMutations,
    types=[configuration.Configuration, oauth.Oauth, oauth.OauthAuthtoken],
)
