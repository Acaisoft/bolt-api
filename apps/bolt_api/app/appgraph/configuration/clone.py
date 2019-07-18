import datetime
import graphene

from flask import current_app

from services.hasura import hce, hce_with_user
from services import gql_util, const


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
    def insert_new_configuration(cloned_configuration_data, user_id, role):
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
        response = hce_with_user(
            current_app.config, query, user_id=user_id, role=role, variable_values=cloned_configuration_data)
        return response['testrun_configuration_create']['returning'][0]

    def mutate(self, info, configuration_id, configuration_name=None):
        role, user_id = gql_util.get_request_role_userid(
            info, (const.ROLE_ADMIN, const.ROLE_TENANT_ADMIN, const.ROLE_MANAGER, const.ROLE_TESTER))
        cloned_configuration_data = Clone.get_cloned_configuration(configuration_id)
        if configuration_name is None:
            date_now = datetime.datetime.now().strftime('%d/%m/%Y | %H:%M:%S')
            configuration_name = '{0} {1}'.format(cloned_configuration_data['name'], date_now)
        cloned_configuration_data['name'] = configuration_name
        new_configuration_data = Clone.insert_new_configuration(cloned_configuration_data, user_id, role)
        return gql_util.OutputValueFromFactory(Clone, {'returning': [{
            'name': new_configuration_data['name'],
            'cloned_configuration_id': configuration_id,
            'new_configuration_id': new_configuration_data['id']
        }]})
