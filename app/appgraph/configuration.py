import graphene

from app.appgraph.util import get_selected_fields, clients
from app.validators import validators
from app.validators.configuration import validate_test_configuration


class RepoUrlInterface(graphene.InputObjectType):
    url = graphene.String()


class ParameterTypeInterface(graphene.InputObjectType):
    param_name = graphene.String(name='param_name')


class ConfigurationParameterInterface(graphene.InputObjectType):
    value = graphene.String()
    parameter = graphene.Field(ParameterTypeInterface)


class ConfigurationInterface(graphene.Interface):
    id = graphene.UUID()
    name = graphene.String()
    repository_id = graphene.String(name='repository_id')
    project_id = graphene.String(name='project_id')


class Configuration(graphene.ObjectType):
    class Meta:
        interfaces = (ConfigurationInterface,)


class CreateConfiguration(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        repository = graphene.Argument(RepoUrlInterface)
        project_id = graphene.UUID(required=True, name='project_id')
        configurationParameters = graphene.List(ConfigurationParameterInterface)

    Output = ConfigurationInterface

    def mutate(self, info, **kwargs):
        validators.validate_name(kwargs['name'])
        validate_test_configuration(kwargs)
        return Configuration()
