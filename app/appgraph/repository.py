import json

import graphene
from flask import current_app
from gql import gql

from app.appgraph.util import get_request_role_userid, ValidationInterface, ValidationResponse
from app import validators, const
from bolt_api.upstream.devclient import devclient


class RepositoryParameterInterface(graphene.InputObjectType):
    name = graphene.String()
    repository_url = graphene.String()
    project_id = graphene.UUID()
    type_id = graphene.UUID()


class RepositoryInterface(graphene.Interface):
    id = graphene.UUID()


class RepositoryType(graphene.ObjectType):
    class Meta:
        interfaces = (RepositoryInterface,)


class Validate(graphene.Mutation):
    """Validates repository configuration."""

    class Arguments:
        name = graphene.String(
            required=True,
            description='Name, unique in this project.')
        repository_url = graphene.String(
            required=True,
            description='Repository address.')
        project_id = graphene.UUID(
            required=True,
            description='Repository project.')
        type_id = graphene.UUID(
            required=True,
            description='Repository type.')

    Output = ValidationInterface

    @staticmethod
    def validate(info, name, repository_url, project_id, type_id):
        role, user_id = get_request_role_userid(info)
        gclient = devclient(current_app.config)

        project_id = str(project_id)
        type_id = str(type_id)

        assert user_id, f'unauthenticated request'
        validators.validate_text(name)

        query = gclient.execute(gql('''query ($projId:uuid!, $repoName:String!, $repoUrl:String!, $userId:uuid!, $confType:uuid!) {
            project(where:{
                id:{_eq:$projId}, 
                userProjects:{user_id:{_eq:$userId}}
            }) { id }
            
            configuration_type_by_pk(id:$confType) { id }
            
            repository(where:{
                project_id:{_eq:$projId},
                _or:{
                    name:{_eq:$repoName},
                    url:{_eq:$repoUrl}
                }
            }) { id }
            
            }'''), {
            'userId': user_id,
            'repoName': name,
            'repoUrl': repository_url,
            'projId': project_id,
            'confType': type_id,

        })
        assert len(query.get('repository')) == 0, f'repository with this name or url already exists'

        if role != const.ROLE_ADMIN:
            assert query.get('project'), \
                f'non-admin ({role}) user {user_id} does not have access to project {project_id}'

        assert query.get('configuration_type_by_pk'), f'type_id does not exist'

        validators.validate_accessibility(repository_url, current_app.config)

        return {
            'name': name,
            'url': repository_url,
            'project_id': project_id,
            'type_id': type_id,
            'created_by_id': user_id,
        }

    def mutate(self, info, name, repository_url, project_id, type_id):
        Validate.validate(info, name, repository_url, project_id, type_id)
        return ValidationResponse(ok=True)


class Create(Validate):
    """Validates and saves configuration for a testrun."""

    Output = RepositoryInterface

    def mutate(self, info, name, repository_url, project_id, type_id):
        gclient = devclient(current_app.config)

        query_params = Validate.validate(info, name, repository_url, project_id, type_id)

        query = gql('''mutation ($data:[repository_insert_input!]!) {
            insert_repository(
                objects: $data
            ) {
                returning { id } 
            }
        }''')
        
        query_response = gclient.execute(query, variable_values={'data': query_params})
        assert query_response['insert_repository'], f'cannot save repository ({str(query_response)})'

        return RepositoryType(id=query_response['insert_project']['returning'][0]['id'])
