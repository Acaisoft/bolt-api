import graphene


class UserQuery(graphene.ObjectType):
    id = graphene.String(argument=graphene.String())
    email = graphene.String(argument=graphene.String())
    active = graphene.Boolean()
    created = graphene.DateTime()


UserSchema = graphene.Schema(query=UserQuery)
