import graphene


class ProjectParameterInterface(graphene.InputObjectType):
    value = graphene.String()
    parameter_id = graphene.UUID(name='parameter_id')


class ProjectInterface(graphene.Interface):
    id = graphene.UUID()
    name = graphene.String()
    description = graphene.String()
    image_url = graphene.String()
