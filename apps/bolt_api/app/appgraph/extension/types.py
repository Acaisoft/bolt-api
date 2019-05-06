import graphene
from services import const


class ExtensionParamType(graphene.AbstractType):
    name = graphene.String()
    value = graphene.String()


class ExtensionParamInterface(ExtensionParamType, graphene.Interface):
    pass


class ExtensionParamInput(ExtensionParamType, graphene.InputObjectType):
    pass


class ExtensionParamObjectType(graphene.ObjectType):
    class Meta:
        interfaces = (ExtensionParamInterface,)


class ExtensionInterface(graphene.Interface):
    id = graphene.UUID()
    configuration_id = graphene.UUID()
    type_slug = graphene.String(description=f'Extension type: "{const.EXTENSION_CHOICE}"')
    params = graphene.List(ExtensionParamObjectType, description='Parameter list.')


class ExtensionType(graphene.ObjectType):
    class Meta:
        interfaces = (ExtensionInterface,)
