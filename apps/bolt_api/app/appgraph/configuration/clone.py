import graphene

from services import gql_util


class CloneInterface(graphene.Interface):
    name = graphene.String()
    cloned_configuration_id = graphene.UUID()
    new_configuration_id = graphene.UUID()


class Clone(graphene.Mutation):

    class Arguments:
        configuration_id = graphene.UUID(required=True, description='ID of cloned configuration')
        configuration_name = graphene.String(required=False, description='New configuration name')

    Output = gql_util.OutputInterfaceFactory(CloneInterface, 'Create')

    def mutate(self, info, configuration_id, configuration_name=None):
        return gql_util.OutputValueFromFactory(Clone, {'returning': [{
            'name': configuration_name,
            'cloned_configuration_id': configuration_id,
            'new_configuration_id': configuration_id
        }]})

