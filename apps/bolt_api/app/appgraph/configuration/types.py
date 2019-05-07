import graphene
from services import const


class ConfigurationParameterAbstractType(graphene.AbstractType):
    value = graphene.String()
    parameter_slug = graphene.String()


class ConfigurationParameterInterface(ConfigurationParameterAbstractType, graphene.Interface):
    pass


class ConfigurationParameterInput(ConfigurationParameterAbstractType, graphene.InputObjectType):
    pass


class ConfigurationParameterType(graphene.ObjectType):
    class Meta:
        interfaces = (ConfigurationParameterInterface,)


class ConfigurationInterface(graphene.Interface):
    id = graphene.UUID()
    name = graphene.String()
    type_slug = graphene.String(
        description=f'Configuration type: "{const.TESTTYPE_LOAD}"')
    project_id = graphene.UUID()
    test_source_id = graphene.UUID(
        required=False,
        description='Test source to fetch test definition from.')
    configuration_parameters = graphene.List(
        ConfigurationParameterInterface,
        description='Default parameter types overrides.')


class ConfigurationType(graphene.ObjectType):
    class Meta:
        interfaces = (ConfigurationInterface,)
    configuration_parameters = graphene.List(
        ConfigurationParameterType,
        description='Default parameter types overrides.')
    runner_parameters = graphene.List(
        ConfigurationParameterType,
        description='Testrunner environment variables.')
