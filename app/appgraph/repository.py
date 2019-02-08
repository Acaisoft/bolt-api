import graphene

from app.appgraph.util import get_selected_fields, clients


class RepositoryInterface(graphene.Interface):
    id = graphene.UUID()
    name = graphene.String()
    url = graphene.String()
    username = graphene.String()
    password = graphene.String()
    user_id = graphene.String()


class Repository(graphene.ObjectType):
    class Meta:
        interfaces = (RepositoryInterface,)


class QueryRepository(graphene.ObjectType):
    repositories = graphene.List(RepositoryInterface)

    def resolve_repositories(self, info):
        return [Repository(**i) for i in clients().repo.query(returning=get_selected_fields(info))]


class CreateRepository(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        active = graphene.Boolean()
    Output = RepositoryInterface

    def mutate(self, info, email, active=False):
        o = clients().user.insert(
            clients().user.input_type(email=email, active=active),
            returning=get_selected_fields(info),
        )
        return Repository(**o[0])
