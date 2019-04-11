import graphene
from flask import current_app
from gql import gql

from app.appgraph.project import types
from app.appgraph.util import get_request_role_userid, ValidationInterface, ValidationResponse, \
    OutputValueFromFactory, OutputInterfaceFactory
from app import const
from app.services import validators
from app.hasura_client import hasura_client


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

    Output = ValidationInterface

    @staticmethod
    def validate(info, name, description=None, image_url=None):
        role, user_id = get_request_role_userid(info, (const.ROLE_ADMIN,))

        gclient = hasura_client(current_app.config)

        validators.validate_text(name)

        projects = gclient.execute(gql('''query ($userId:uuid!, $name:String!) {
            project (where:{name:{_eq:$name}, userProjects:{user_id:{_eq:$userId}}}) {
                name
            }
        }'''), {
            'userId': user_id,
            'name': name,
        })
        assert len(projects.get('project', None)) == 0, f'project with this name already exists'

        if description:
            description = validators.validate_text(description, key='description', required=False)

        if image_url:
            validators.validate_url(image_url, key='image_url', required=False)
            image_url = image_url.strip()

        return {
            'name': name,
            'description': description,
            'image_url': image_url,
            'created_by_id': user_id,
        }

    def mutate(self, info, name, description=False, image_url=None):
        CreateValidate.validate(info, name, description, image_url)
        return ValidationResponse(ok=True)


class Create(CreateValidate):
    """Validates and saves configuration for a project."""

    Output = OutputInterfaceFactory(types.ProjectInterface, 'Create')

    def mutate(self, info, name, description=None, image_url=None):
        _, user_id = get_request_role_userid(info, (const.ROLE_ADMIN,))

        gclient = hasura_client(current_app.config)

        query_params = CreateValidate.validate(info, name, description, image_url)

        query = gql('''mutation ($data:[project_insert_input!]!) {
            insert_project(
                objects: $data
            ) {
                returning { id name description } 
            }
        }''')

        conf_response = gclient.execute(query, variable_values={'data': query_params})
        assert conf_response['insert_project'], f'cannot save project ({str(conf_response)})'

        proj_id = conf_response['insert_project']['returning'][0]['id']

        gclient.execute(gql('''mutation ($data:[user_project_insert_input!]!){
            insert_user_project (objects:$data) { affected_rows }
        }'''), variable_values={'data': {
            'user_id': str(user_id),
            'project_id': proj_id,
        }})

        return OutputValueFromFactory(Create, conf_response['insert_project'])
