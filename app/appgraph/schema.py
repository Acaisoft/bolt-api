import graphene

from app.appgraph import configuration


class RootQuery(configuration.QueryConfiguration):
    pass


class RootMutations(graphene.ObjectType):
    create_configuration = configuration.CreateConfiguration.Field()


AppSchema = graphene.Schema(
    query=RootQuery,
    mutation=RootMutations,
    types=[configuration.Configuration],
)
