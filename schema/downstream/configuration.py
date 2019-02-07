import graphene

from schema.downstream.util import get_selected_fields, clients


class ConfigurationInterface(graphene.Interface):
    id = graphene.UUID()
    name = graphene.String()
    repository_id = graphene.String()
    project_id = graphene.String()
    type_id = graphene.String()


class Configuration(graphene.ObjectType):
    class Meta:
        interfaces = (ConfigurationInterface,)


class QueryConfiguration(graphene.ObjectType):
    conf = graphene.Field(
        ConfigurationInterface,
        required=False,
        conf_id=graphene.UUID(required=True),
    )
    confs = graphene.List(ConfigurationInterface)

    def resolve_conf(self, info, conf_id=None):
        if conf_id:
            print(info.return_type.fields)
            o = clients().conf.query(
                where=f'(where:{{id:{{_eq: "{conf_id}" }} }})',
                returning=get_selected_fields(info),
            )
            return Configuration(**o[0])

    def resolve_confs(self, info):
        o = clients().conf.query(
            where=f'(where:{{ project_id:{{ _in:[] }} }}',
            returning=get_selected_fields(info),
        )
        return [Configuration(**i) for i in o]


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
