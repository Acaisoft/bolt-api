import graphene
from flask import current_app
from gql import gql

from app.appgraph.project import types
from app.appgraph.util import get_request_role_userid, ValidationInterface, ValidationResponse, \
    OutputValueFromFactory, OutputInterfaceFactory
from app import const
from app.services import validators
from app.hasura_client import hasura_client


class UpdateValidate(graphene.Mutation):
    """Validates project update parameters."""

    class Arguments:
        id = graphene.UUID(
            description='Project id')
        name = graphene.String(
            required=False,
            description='Name, unique for user.')
        description = graphene.String(
            required=False,
            description='Project description.')
        image_url = graphene.String(
            required=False,
            description='Project logo.')

    Output = ValidationInterface

    @staticmethod
    def validate(info, id, name=None, description=None, image_url=None):
        role, user_id = get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_MANAGER,))

        gclient = hasura_client(current_app.config)

        if name:
            name = validators.validate_text(name)

        projects = gclient.execute(gql('''query ($projId:uuid!, $userId:uuid!, $name:String!) {
            original: project_by_pk(id:$projId) { id name }
            
            uniqueName: project (where:{name:{_eq:$name}, userProjects:{user_id:{_eq:$userId}}}) {
                name
            }
        }'''), {
            'projId': str(id),
            'userId': user_id,
            'name': name or '',
        })
        assert projects.get('original'), f'project {str(id)} does not exist'

        query_params = {}

        if name and name != projects.get('original')['name']:
            query_params['name'] = name.strip()
            assert len(projects.get('uniqueName', None)) == 0, f'project with this name already exists'

        if description:
            validators.validate_text(description, key='description', required=False)
            query_params['description'] = description.strip()

        if image_url:
            validators.validate_url(image_url, key='image_url', required=False)
            query_params['image_url'] = image_url.strip()

        return query_params

    def mutate(self, info, id, name, description, image_url):
        UpdateValidate.validate(info, id, name, description, image_url)
        return ValidationResponse(ok=True)


class Update(UpdateValidate):
    """Validates and updates a project."""

    Output = OutputInterfaceFactory(types.ProjectInterface, 'Update')

    def mutate(self, info, id, name=None, description=None, image_url=None):
        gclient = hasura_client(current_app.config)

        query_params = UpdateValidate.validate(info, id, name, description, image_url)

        query = gql('''mutation ($id:uuid!, $data:project_set_input!) {
            update_project(
                where:{id:{_eq:$id}},
                _set: $data
            ) {
                returning { id name description image_url } 
            }
        }''')

        conf_response = gclient.execute(query, variable_values={'id': str(id), 'data': query_params})
        assert conf_response['update_project'], f'cannot update project ({str(conf_response)})'

        return OutputValueFromFactory(Update, conf_response['update_project'])
