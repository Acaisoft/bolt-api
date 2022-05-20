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
