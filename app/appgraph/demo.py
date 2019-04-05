import graphene
from flask import current_app
from gql import gql

from app.appgraph.util import get_request_role_userid
from app import const
from app.hasura_client import hasura_client
from app.services.demo.demo_project import setup_demo_project


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
            delete_configuration_parameter (where:{configuration:{project_id:{_in:$projIds}}}) {affected_rows}
            delete_result_error (where:{execution:{configuration:{project_id:{_in:$projIds}}}}) {affected_rows}
            delete_result_distribution (where:{execution:{configuration:{project_id:{_in:$projIds}}}}) {affected_rows}
            delete_result_aggregate (where:{execution:{configuration:{project_id:{_in:$projIds}}}}) {affected_rows}
            delete_execution (where:{configuration:{project_id:{_in:$projIds}}}) {affected_rows}
            delete_configuration (where:{project_id:{_in:$projIds}}) {affected_rows}
            delete_test_source(where:{project_id:{_in:$projIds}}) { affected_rows }
            delete_test_creator (where:{project_id:{_in:$projIds}}) {affected_rows}
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
        role, user_id = get_request_role_userid(info)
        assert user_id, f'unauthenticated request'
        assert role == const.ROLE_ADMIN, f'{role} user cannot create projects'

        if not req_user_id:
            req_user_id = user_id
        else:
            req_user_id = str(req_user_id)

        project_id = setup_demo_project(name, req_user_id)

        return DemoProject(project_id=project_id)
