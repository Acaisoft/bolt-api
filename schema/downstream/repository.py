import graphene

from schema.downstream.util import get_selected_fields, clients


class RepositoryInterface(graphene.Interface):
    id = graphene.UUID()
    name = graphene.String(required=True)
    url = graphene.String(required=True)
    username = graphene.String(required=True)
    password = graphene.String(required=True)
    user_id = graphene.String(required=True)


class Repository(graphene.ObjectType):
    class Meta:
        interfaces = (RepositoryInterface,)


class QueryRepository(graphene.ObjectType):
    repository = graphene.Field(
        RepositoryInterface,
        required=False,
        repo_id=graphene.UUID(required=True),
    )
    repositories = graphene.List(RepositoryInterface)

    def resolve_repository(self, info, repo_id=None):
        if repo_id:
            o = clients().repo.query(
                where=f'(where:{{id:{{_eq: "{repo_id}" }} }})',
                returning=get_selected_fields(info),
            )
            return Repository(**o[0])

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
