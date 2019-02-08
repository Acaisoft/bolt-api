import graphene

from app.appgraph import configuration
from app.appgraph import user, repository


class RootQuery(user.QueryUser, repository.QueryRepository, configuration.QueryConfiguration):
    pass


class RootMutations(graphene.ObjectType):
    create_user = user.CreateUser.Field()
    create_repository = repository.CreateRepository.Field()
    create_configuration = configuration.CreateConfiguration.Field()


AppSchema = graphene.Schema(
    query=RootQuery,
    mutation=RootMutations,
    types=[user.User, repository.Repository, configuration.Configuration],
)
