import graphene

from app.appgraph import configuration
from app.appgraph.oauth import QueryOauth


class RootQuery(configuration.QueryConfiguration, QueryOauth):
    pass


class RootMutations(graphene.ObjectType):
    create_configuration = configuration.CreateConfiguration.Field()


AppSchema = graphene.Schema(
    query=RootQuery,
    mutation=RootMutations,
    types=[configuration.Configuration],
)
