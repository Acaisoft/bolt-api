import graphene

from app.appgraph.util import get_selected_fields, clients


class ConfigurationInterface(graphene.Interface):
    id = graphene.UUID()
    name = graphene.String()
    repository_id = graphene.String()
    project_id = graphene.String()
    type_id = graphene.String()


class Configuration(graphene.ObjectType):
    class Meta:
        interfaces = (ConfigurationInterface,)


class CreateConfiguration(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        repository_id = graphene.UUID(required=True)
        project_id = graphene.UUID(required=True)
        type_id = graphene.UUID(required=True)

    Output = ConfigurationInterface

    def mutate(self, info, **kwargs):
        o = clients().conf.insert(
            clients().conf.input_type(**kwargs),
            returning=get_selected_fields(info),
        )
        return Configuration(**o[0])
