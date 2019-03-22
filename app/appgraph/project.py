import json
import uuid
from datetime import timedelta, datetime

import graphene
from flask import current_app
from gql import gql

from app.appgraph.util import get_request_role_userid, ValidationInterface, ValidationResponse, OutputTypeFactory, \
    OutputValueFromFactory, OutputInterfaceFactory
from app import validators, const
from app.hasura_client import hasura_client

from google.cloud import storage
from google.cloud.storage._signing import generate_signed_url


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

        if name:
            validators.validate_text(name)

        projects = gclient.execute(gql('''query ($projId:uuid!, $userId:uuid!, $name:String!) {
            original: project_by_pk(id:$projId) { id }
            
            uniqueName: project (where:{name:{_eq:$name}, userProjects:{user_id:{_eq:$userId}}}) {
                name
            }
        }'''), {
            'projId': str(id),
            'userId': user_id,
            'name': name or '',
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
            description='Base64 encoded file content MD5 hash')

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
        # test uploading file.jpg using curl, openssl, and graphql helper cli:
        # export BASE64MD5=`cat file.jpg | openssl dgst -md5 -binary  | openssl enc -base64
        # export UPLOAD_URL=graphiql_cli.testrun_project_image_upload(content_type="image/jpeg", content_md5=$BASE64MD5, id="123").response.data.upload_url
        # curl -v -X PUT -H "Content-Type: image/jpeg" -H "Content-MD5: $BASE64MD5" -T - $UPLOAD_URL < file.jpg
        ImageUploadUrl.validate(info, id, content_type, content_md5)

        project_logos_bucket = current_app.config.get('BUCKET_PUBLIC_UPLOADS', 'project_logos_bucket')

        upload_url = generate_signed_url(
            credentials=storage.Client()._credentials,
            api_access_endpoint='https://storage.googleapis.com',  # change to domain configured to point to project_logos_bucket
            resource=f'/{project_logos_bucket}/project_logos/{str(id)}',
            method='PUT',
            expiration=datetime.now() + timedelta(minutes=15),
            content_md5=content_md5,
            content_type=content_type,
        )

        return OutputValueFromFactory(ImageUploadUrl, {'returning': [{
            'id': id,
            'upload_url': upload_url,
            'download_url': upload_url.split('?')[0],
        }]})


class PurgeProject(graphene.Mutation):
    """DO NOT USE. Purges project and all related objects from database."""

    class Arguments:
        project_id = graphene.UUID(required=False)
        project_name = graphene.String(required=False, description='Accepts an sql-style wildcard')

    deleted_projects = graphene.List(graphene.UUID)

    def mutate(self, info, project_id=None, project_name=None):
        assert not all((project_id, project_name)), f'use either id or name, not both'

        role, user_id = get_request_role_userid(info)
        assert user_id, f'unauthenticated request'
        assert role == const.ROLE_ADMIN, f'{role} user cannot create projects'

        gclient = hasura_client(current_app.config)

        if project_name:
            projects = gclient.execute(
                gql('''query ($name:String!) { project(where:{name:{_ilike:$name}}) { id } }'''),
                variable_values={'name': project_name}
            )
            project_ids_list = [str(x['id']) for x in projects['project']]
        else:
            project_ids_list = [str(project_id)]

        output = gclient.execute(gql('''mutation ($projIds:[uuid!]!) {
            delete_test_source(where:{project_id:{_in:$projIds}}) { affected_rows }
            delete_test_creator_configuration_m2m (where:{project_id:{_in:$projIds}}) {affected_rows}
            delete_test_creator (where:{test_creator_configuration_m2m:{project_id:{_in:$projIds}}}) {affected_rows}
            delete_configuration_parameter (where:{configuration:{project_id:{_in:$projIds}}}) {affected_rows}
            delete_result_error (where:{execution:{configuration:{project_id:{_in:$projIds}}}}) {affected_rows}
            delete_result_distribution (where:{execution:{configuration:{project_id:{_in:$projIds}}}}) {affected_rows}
            delete_result_aggregate (where:{execution:{configuration:{project_id:{_in:$projIds}}}}) {affected_rows}
            delete_execution (where:{configuration:{project_id:{_in:$projIds}}}) {affected_rows}
            delete_configuration (where:{project_id:{_in:$projIds}}) {affected_rows}
            delete_repository (where:{project_id:{_in:$projIds}}) {affected_rows}
            delete_user_project (where:{project_id:{_in:$projIds}}) {affected_rows}
            delete_project(where:{id:{_in:$projIds}}) {affected_rows}
        }'''), variable_values={'projIds': project_ids_list})

        return PurgeProject(deleted_projects=project_ids_list)


class DemoProject(graphene.Mutation):
    """DO NOT USE. Debug use only. Creates a project with minimal data in database."""

    class Arguments:
        name = graphene.String()
        req_user_id = graphene.UUID(required=False)

    project_id = graphene.UUID()

    def mutate(self, info, name, req_user_id=None):
        # TODO: add some test_creator inputs when ready, maybe some

        UUID = str(uuid.uuid4())
        if not req_user_id:
            req_user_id = UUID
        role, user_id = get_request_role_userid(info)
        assert user_id, f'unauthenticated request'
        assert role == const.ROLE_ADMIN, f'{role} user cannot create projects'

        gclient = hasura_client(current_app.config)

        gclient.execute(gql('''mutation ($id:uuid!, $id2:uuid!, $userId:uuid!, $name:String!, $timestamp:timestamptz!) {
            insert_project (objects:[{id:$id, name:$name}]) {affected_rows}
            insert_user_project (objects:[{id:$id,, project_id:$id, user_id:$userId}]) {affected_rows}
            insert_good_repository: insert_repository (objects:[{id:$id, name:$name, project_id:$id, url:"git@bitbucket.org:acaisoft/load-events.git", type_slug:"load_tests"}]) {affected_rows}
            insert_bad_repository: insert_repository (objects:[{id:$id2, name:"some repo", project_id:$id, url:"git@bitbucket.org:acaisoft/invalid-url.git", type_slug:"load_tests"}]) {affected_rows}
            insert_good_conf_repository: insert_configuration (objects:[{id:$id, name:$name, project_id:$id, repository_id:$id, code_source:"repository", type_slug:"load_tests"}]) {affected_rows}
            insert_bad_conf_repository: insert_configuration (objects:[{name:"conf with some repo", project_id:$id, repository_id:$id2, code_source:"repository", type_slug:"load_tests"}]) {affected_rows}
            insert_execution (objects:[{id:$id, configuration_id:$id, status:"INIT"}]) {affected_rows}
            insert_result_aggregate (objects:[{execution_id:$id, average_response_time:10, number_of_successes:100, number_of_errors:20, number_of_fails:30, average_response_size:1234}]) {affected_rows}
            insert_result_distribution (objects:[{execution_id:$id, request_result:"{}", distribution_result:"{}", start:$timestamp, end:$timestamp}]) {affected_rows}
            insert_result_error (objects:[{execution_id:$id, error_type:"AssertionError", name:$name, exception_data:"tralala", number_of_occurrences:120}]) {affected_rows}
            insert_host: insert_configuration_parameter (objects:[{configuration_id:$id, parameter_slug:"load_tests_host", value:"https://att-lwd-go-dev.acaisoft.net/api"}]) {affected_rows}
            insert_duration: insert_configuration_parameter (objects:[{configuration_id:$id, parameter_slug:"load_tests_duration", value:"15"}]) {affected_rows}
            insert_conf_creator: insert_configuration (objects:[{id:$id2, name:$name, project_id:$id, code_source:"creator", type_slug:"load_tests"}]) {affected_rows}
            insert_test_creator(objects:[{ id:$id, max_wait:200, min_wait:100, data:{} }]) { affected_rows }
            insert_test_creator_configuration_m2m(objects:[{id:$id, configuration_id:$id2, name:$name, type_slug:"load_tests", project_id:$id }]) { affected_rows }
            
            source_1: insert_test_source(objects:[{ project_id:$id, source_type:"creator", test_creator_id:$id }]) { affected_rows }
            source_2: insert_test_source(objects:[{ project_id:$id, source_type:"repository", repository_id:$id }]) { affected_rows }
            source_3: insert_test_source(objects:[{ project_id:$id, source_type:"repository", repository_id:$id2 }]) { affected_rows }
            
        }'''), variable_values={'id': UUID, 'id2': str(uuid.uuid4()), 'name': name, 'userId': str(req_user_id), 'timestamp': datetime.now().astimezone().isoformat()})

        return DemoProject(project_id=UUID)
