import graphene
from flask import current_app

from apps.bolt_api.app.appgraph.project import types
from services import const, gql_util
from services import validators
from services.hasura import hce


class CreateValidate(graphene.Mutation):
    """Validates configuration for a testrun. Ensures repository is accessible and test parameters are sane."""

    class Arguments:
        name = graphene.String(
            required=True,
            description='Name, unique for user.')
        description = graphene.String(
            required=False,
            description='Project description.')
        image_url = graphene.String(
            required=False,
            description='Project logo.')

    Output = gql_util.ValidationInterface

    @staticmethod
    def validate(info, name, description=None, image_url=None):
        role, user_id = gql_util.get_request_role_userid(info, (const.ROLE_ADMIN,))

        validators.validate_text(name)

        projects = hce(current_app.config, '''query ($userId:uuid!, $name:String!) {
            project (where:{
                name:{_eq:$name},
                is_deleted: {_eq:false}, 
                userProjects:{user_id:{_eq:$userId}}
            }) {
                name
            }
        }''', {
            'userId': user_id,
            'name': name,
        })
        assert len(projects.get('project', None)) == 0, f'project with this name already exists'

        if description:
            description = validators.validate_text(description, key='description', required=False)

        if image_url:
            image_url = validators.validate_url(image_url, key='image_url', required=False)

        return {
            'name': name,
            'description': description,
            'image_url': image_url,
            'created_by_id': user_id,
        }

    def mutate(self, info, name, description=False, image_url=None):
        CreateValidate.validate(info, name, description, image_url)
        return gql_util.ValidationResponse(ok=True)


class Create(CreateValidate):
    """Validates and saves configuration for a project."""

    Output = gql_util.OutputInterfaceFactory(types.ProjectInterface, 'Create')

    def mutate(self, info, name, description=None, image_url=None):
        _, user_id = gql_util.get_request_role_userid(info, (const.ROLE_ADMIN,))

        query_params = CreateValidate.validate(info, name, description, image_url)

        query = '''mutation ($data:[project_insert_input!]!) {
            insert_project(
                objects: $data
            ) {
                returning { id name description } 
            }
        }'''

        conf_response = hce(current_app.config, query, variable_values={'data': query_params})
        assert conf_response['insert_project'], f'cannot save project ({str(conf_response)})'

        proj_id = conf_response['insert_project']['returning'][0]['id']

        hce(current_app.config, '''mutation ($data:[user_project_insert_input!]!){
            insert_user_project (objects:$data) { affected_rows }
        }''', variable_values={'data': {
            'user_id': str(user_id),
            'project_id': proj_id,
        }})

        return gql_util.OutputValueFromFactory(Create, conf_response['insert_project'])
