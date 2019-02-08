import graphene

from app.appgraph.util import get_selected_fields, clients


class UserInterface(graphene.Interface):
    id = graphene.UUID()
    email = graphene.String()
    active = graphene.Boolean()
    created = graphene.DateTime()


class User(graphene.ObjectType):
    class Meta:
        interfaces = (UserInterface,)


class QueryUser(graphene.ObjectType):
    users = graphene.List(UserInterface)

    def resolve_users(self, info):
        return [User(**i) for i in clients().user.query(returning=get_selected_fields(info))]


class CreateUser(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        active = graphene.Boolean()
    Output = UserInterface

    def mutate(self, info, email, active=False):
        o = clients().user.insert(
            clients().user.input_type(email=email, active=active),
            returning=get_selected_fields(info),
        )
        return User(**o[0])
