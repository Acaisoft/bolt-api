import json

import graphene
from flask import current_app
from gql import gql

from app.appgraph.util import get_request_role_userid, ValidationInterface, ValidationResponse, OutputTypeFactory, \
    OutputValueFromFactory, OutputInterfaceFactory
from app import validators, const
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
    def validate(info, name, description, image_url):
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
            validators.validate_text(description, key='description', required=False)

        if image_url:
            validators.validate_url(image_url, key='image_url', required=False)
            file_extension = image_url.split('.')[-1]
            assert file_extension.lower() in (
                'jpg', 'jpeg', 'png', 'gif'), f'unsupported image_url file type {file_extension}'

        return {
            'name': name,
            'description': description,
            'image_url': image_url,
            'created_by_id': user_id,
        }

    def mutate(self, info, name, description="", image_url=""):
        CreateValidate.validate(info, name, description, image_url)
        return ValidationResponse(ok=True)


class Create(CreateValidate):
    """Validates and saves configuration for a testrun."""

    Output = OutputInterfaceFactory(ProjectInterface, 'Create')

    def mutate(self, info, name, description="", image_url=""):
        _, user_id = get_request_role_userid(info)

        gclient = hasura_client(current_app.config)

        query_params = CreateValidate.validate(info, name, description, image_url)

        query = gql('''mutation ($data:[project_insert_input!]!) {
            insert_project(
                objects: $data
            ) {
                returning { id name description image_url } 
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

        validators.validate_text(name)

        projects = gclient.execute(gql('''query ($projId:uuid!, $userId:uuid!, $name:String!) {
            original: project_by_pk(id:$projId) { id }
            
            uniqueName: project (where:{name:{_eq:$name}, userProjects:{user_id:{_eq:$userId}}}) {
                name
            }
        }'''), {
            'projId': str(id),
            'userId': user_id,
            'name': name,
        })
        assert projects.get('original'), f'project {str(id)} does not exist'

        assert len(projects.get('uniqueName', None)) == 0, f'project with this name already exists'

        query_params = {}

        if name:
            query_params['name'] = name.strip()

        if description:
            validators.validate_text(description, key='description', required=False)
            query_params['description'] = description.strip()

        if image_url:
            validators.validate_url(image_url, key='image_url', required=False)
            file_extension = image_url.split('.')[-1]
            assert file_extension.lower() in (
                'jpg', 'jpeg', 'png', 'gif'), f'unsupported image_url file type {file_extension}'
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


class UploadUrlReturnType(graphene.ObjectType):
    id = graphene.UUID()
    upload_url = graphene.String()
    download_url = graphene.String()


class ImageUploadUrl(graphene.Mutation):
    """Generate project image upload url."""

    class Arguments:
        id = graphene.UUID(
            description='Project id')
        content_type = graphene.String(
            description='File mime type')
        content_md5 = graphene.String(
            description='File content MD5 hash')

    Output = OutputTypeFactory(UploadUrlReturnType)

    @staticmethod
    def validate(info, id, content_type, content_md5):
        role, user_id = get_request_role_userid(info)
        assert user_id, f'unauthenticated request'
        assert role in (const.ROLE_ADMIN, const.ROLE_MANAGER), f'user with role {role} cannot update projects'

        gclient = hasura_client(current_app.config)

        projects = gclient.execute(gql('''query ($projId:uuid!, $userId:uuid!) {
            project (where:{id:{_eq:$projId}, userProjects:{user_id:{_eq:$userId}}}) { id }
        }'''), {
            'projId': str(id),
            'userId': user_id,
        })
        assert len(projects.get('project', [])), f'project {str(id)} does not exist or user is not authorized'

        assert content_type in const.IMAGE_CONTENT_TYPES, f'illegal content_type "{content_type}", valid choices are: {const.IMAGE_CONTENT_TYPES}'

        assert content_md5 and len(content_md5) > 10, f'invalid content_md5'

    def mutate(self, info, id, content_type, content_md5):
        ImageUploadUrl.validate(info, id, content_type, content_md5)

        # TODO: get the urls

        return OutputValueFromFactory(ImageUploadUrl, {'returning': [{
            'id': id,
            'upload_url': 'https://duckduckgo.com/i/16664acd.png',
            'download_url': 'https://duckduckgo.com/i/bdff2324.png',
        }]})
