import graphene
from flask import current_app
from gql import gql

from app.appgraph.util import get_request_role_userid, ValidationInterface, ValidationResponse, \
    OutputValueFromFactory, OutputInterfaceFactory
from app import const
from app.services import validators
from app.hasura_client import hasura_client


class ProjectParameterInterface(graphene.InputObjectType):
    value = graphene.String()
    parameter_id = graphene.UUID(name='parameter_id')


class ProjectInterface(graphene.Interface):
    id = graphene.UUID()
    name = graphene.String()
    description = graphene.String()
    image_url = graphene.String()


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
        role, user_id = get_request_role_userid(info)
        assert user_id, f'unauthenticated request'
        assert role == const.ROLE_ADMIN, f'user with role {role} cannot create projects'

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
    """Validates and saves configuration for a testrun."""

    Output = OutputInterfaceFactory(ProjectInterface, 'Create')

    def mutate(self, info, name, description=None, image_url=None):
        _, user_id = get_request_role_userid(info)

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
        role, user_id = get_request_role_userid(info)
        assert user_id, f'unauthenticated request'
        assert role in (const.ROLE_ADMIN, const.ROLE_MANAGER), f'user with role {role} cannot update projects'

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

    Output = OutputInterfaceFactory(ProjectInterface, 'Update')

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
