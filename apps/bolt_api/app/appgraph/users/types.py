import graphene


class GetProjectInvitationInterface(graphene.Interface):
    token = graphene.String()


class SimpleStatusInterface(graphene.Interface):
    success = graphene.Boolean()


class UserInterface(graphene.Interface):
    id = graphene.UUID()
    email = graphene.String()
    project_id = graphene.UUID()
    role = graphene.String()


class UserListItemInterface(graphene.Interface):
    id = graphene.UUID()
    username = graphene.String()
    email_verified = graphene.Boolean()
    email = graphene.String()
    bolt_roles = graphene.List(graphene.String)


class UserListItemType(graphene.ObjectType):
    class Meta:
        interfaces = [UserListItemInterface]


class UserListInterface(graphene.Interface):
    project_id = graphene.UUID()
    users = graphene.List(UserListItemType)


class UserListType(graphene.ObjectType):
    class Meta:
        interfaces = [UserListInterface]