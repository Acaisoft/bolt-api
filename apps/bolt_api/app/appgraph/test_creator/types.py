import graphene


class TestCreatorInterface(graphene.Interface):
    id = graphene.UUID()


class TestCreatorType(graphene.ObjectType):
    class Meta:
        interfaces = (TestCreatorInterface,)
