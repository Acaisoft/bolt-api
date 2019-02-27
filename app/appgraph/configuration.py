import json

import graphene
from flask import current_app
from gql import gql

from app.appgraph.util import get_selected_fields, clients, get_request_role_userid
from app import validators, const
from bolt_api.upstream.devclient import devclient


class ConfigurationParameterInterface(graphene.InputObjectType):
    value = graphene.String()
    parameter_id = graphene.UUID(name='parameter_id')


class ConfigurationInterface(graphene.Interface):
    id = graphene.UUID()


class Configuration(graphene.ObjectType):
    class Meta:
        interfaces = (ConfigurationInterface,)


class CreateConfiguration(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        repository_id = graphene.String(required=True, name='repository_id')
        project_id = graphene.UUID(required=True, name='project_id')
        configuration_parameters = graphene.List(ConfigurationParameterInterface)

    Output = ConfigurationInterface

    def mutate(self, info, name, repository_id, project_id, configuration_parameters):
        role, user_id = get_request_role_userid(info)
        gclient = devclient(current_app.config)
        repo = gclient.execute(gql('''query ($repoId:uuid!, $projId:uuid!, $userId:uuid!) {
            repository_by_pk(id:$repoId) {
                url
                configurationType { slug_name }
                project {
                    is_deleted
                    userProjects { user_id }
                }
            }
            parameter {
                id
                default_value
                param_name
                name
            }
            user_project (where:{ user_id:{_eq:$userId}, project_id:{_eq:$projId} }) {
                id
            }
        }'''), {
            'repoId': str(repository_id),
            'projId': str(project_id),
            'userId': user_id,
        })
        assert repo.get('repository_by_pk', None), f'repository does not exist'

        if role != const.ROLE_ADMIN:
            assert repo.get('user_project', None), f'non-admin ({role}) user {user_id} does not have access to project {str(project_id)}'

        validators.validate_repository(user_id=user_id, repo_config=repo['repository_by_pk'])

        validators.validate_accessibility(repo['repository_by_pk']['url'], current_app.config)

        validators.validate_name(name)

        patched_params = validators.validate_test_params(configuration_parameters, defaults=repo['parameter'])

        query_params = {
            'name': name,
            'repository_id': str(repository_id),
            'project_id': str(project_id),
            'configurationParameters': {'data': []},
            'created_by_id': user_id,
        }

        for param_id, param_value in patched_params.items():
            query_params['configurationParameters']['data'].append({
                'parameter_id': param_id,
                'value': param_value,
            })

        query = gql('''mutation ($data:[configuration_insert_input!]!) {
            insert_configuration(
                objects: $data
            ) {
                returning { id } 
            }
        }''')
        conf_response = gclient.execute(query, variable_values={'data': query_params})
        assert conf_response['insert_configuration'], f'cannot save configuration ({str(conf_response)})'

        return Configuration(id=conf_response['insert_configuration']['returning'][0]['id'])
