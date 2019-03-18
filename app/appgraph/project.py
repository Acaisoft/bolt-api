import graphene
from flask import current_app
from gql import gql

from app.appgraph.util import get_request_role_userid, ValidationInterface, ValidationResponse
from app import validators
from app.hasura_client import hasura_client


class ProjectParameterInterface(graphene.InputObjectType):
    value = graphene.String()
    parameter_id = graphene.UUID(name='parameter_id')


class ProjectInterface(graphene.Interface):
    id = graphene.UUID()


class ProjectType(graphene.ObjectType):
    class Meta:
        interfaces = (ProjectInterface,)


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
        contact = graphene.String(
            required=False,
            description='Project POC.')

    Output = ValidationInterface

    @staticmethod
    def validate(info, name, description, image_url, contact):
        role, user_id = get_request_role_userid(info)
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

        validators.validate_text(description, key='description', required=False)

        validators.validate_url(image_url, key='image_url', required=False)

        if image_url:
            file_extension = image_url.split('.')[-1]
            assert file_extension.lower() in ('jpg', 'jpeg', 'png', 'gif'), f'unsupported image_url file type {file_extension}'

        return {
            'name': name,
            'description': description,
            'image_url': image_url,
            'contact': contact,
            'created_by_id': user_id,
        }

    def mutate(self, info, name, description, image_url, contact):
        CreateValidate.validate(info, name, description, image_url, contact)
        return ValidationResponse(ok=True)


class Create(CreateValidate):
    """Validates and saves configuration for a testrun."""

    Output = ProjectInterface

    def mutate(self, info, name, description, image_url, contact):
        gclient = hasura_client(current_app.config)

        query_params = CreateValidate.validate(info, name, description, image_url, contact)

        query = gql('''mutation ($data:[project_insert_input!]!) {
            insert_project(
                objects: $data
            ) {
                returning { id } 
            }
        }''')
        
        conf_response = gclient.execute(query, variable_values={'data': query_params})
        assert conf_response['insert_project'], f'cannot save project ({str(conf_response)})'

        return ProjectType(id=conf_response['insert_project']['returning'][0]['id'])


class UpdateValidate(graphene.Mutation):
    """Validates project update parameters."""

    class Arguments:
        id = graphene.UUID(
            description='Configuration object id')
        name = graphene.String(
            required=False,
            description='Name, unique for user.')
        description = graphene.String(
            required=False,
            description='Project description.')
        image_url = graphene.String(
            required=False,
            description='Project logo.')
        contact = graphene.String(
            required=False,
            description='Project POC.')

    Output = ValidationInterface

    @staticmethod
    def validate(info, id, name, description, image_url, contact):
        role, user_id = get_request_role_userid(info)
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

        validators.validate_text(description, key='description', required=False)

        validators.validate_url(image_url, key='image_url', required=False)

        if image_url:
            file_extension = image_url.split('.')[-1]
            assert file_extension.lower() in ('jpg', 'jpeg', 'png', 'gif'), f'unsupported image_url file type {file_extension}'

        return {
            'name': name,
            'description': description,
            'image_url': image_url,
            'contact': contact,
            'created_by_id': user_id,
        }

    def mutate(self, info, id, name, description, image_url, contact):
        UpdateValidate.validate(info, id, name, description, image_url, contact)
        return ValidationResponse(ok=True)


class Update(UpdateValidate):
    """Validates and saves configuration for a testrun."""

    Output = ProjectInterface

    def mutate(self, info, id, name, description, image_url, contact):
        gclient = hasura_client(current_app.config)

        query_params = UpdateValidate.validate(info, id, name, description, image_url, contact)

        query = gql('''mutation ($data:[project_insert_input!]!) {
            insert_project(
                objects: $data
            ) {
                returning { id } 
            }
        }''')

        conf_response = gclient.execute(query, variable_values={'data': query_params})
        assert conf_response['insert_project'], f'cannot save project ({str(conf_response)})'

        return ProjectType(id=conf_response['insert_project']['returning'][0]['id'])
