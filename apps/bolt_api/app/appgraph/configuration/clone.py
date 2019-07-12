import graphene

from flask import current_app

from services.hasura import hce
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

    @staticmethod
    def get_cloned_configuration(_id):
        query = '''
            query ($id: uuid) {
              configuration(where: {id: {_eq: $id}}) {
                name
                project_id
                type_slug
                test_source_id
                has_pre_test
                has_post_test
                has_load_tests
                has_monitoring
                monitoring_chart_configuration
                configuration_envvars{
                  name
                  value
                }
                configuration_parameters{
                  value
                  parameter_slug
                }
              }
            }
        '''
        response = hce(current_app.config, query, variable_values={'id': str(_id)})
        return response['configuration'][0]

    @staticmethod
    def insert_new_configuration(cloned_configuration_data):
        query = '''
            mutation (
                $name: String!, 
                $type_slug: String!, 
                $project_id: UUID!, 
                $test_source_id: UUID, 
                $has_pre_test: Boolean, 
                $has_post_test: Boolean, 
                $has_load_tests: Boolean, 
                $has_monitoring: Boolean
                $configuration_envvars: [ConfigurationEnvVarInput], 
                $configuration_parameters: [ConfigurationParameterInput]) {    
                    testrun_configuration_create(
                        name: $name, 
                        type_slug: $type_slug, 
                        project_id: $project_id, 
                        test_source_id: $test_source_id, 
                        has_pre_test: $has_pre_test, 
                        has_post_test: $has_post_test, 
                        has_load_tests: $has_load_tests, 
                        has_monitoring: $has_monitoring,
                        configuration_envvars: $configuration_envvars,
                        configuration_parameters: $configuration_parameters) {
                            affected_rows
                            returning {
                                id
                                name
                            }
                    }
            }
        '''
        response = hce(current_app.config, query, variable_values=cloned_configuration_data)
        return response['testrun_configuration_create']['returning'][0]

    def mutate(self, info, configuration_id, configuration_name=None):
        cloned_configuration_data = Clone.get_cloned_configuration(configuration_id)
        if configuration_name is not None:
            cloned_configuration_data['name'] = configuration_name
        else:
            cloned_configuration_data['name'] = '{0} {1}'.format(cloned_configuration_data['name'], '(CLONED)')
        new_configuration_data = Clone.insert_new_configuration(cloned_configuration_data)
        return gql_util.OutputValueFromFactory(Clone, {'returning': [{
            'name': new_configuration_data['name'],
            'cloned_configuration_id': configuration_id,
            'new_configuration_id': new_configuration_data['id']
        }]})
