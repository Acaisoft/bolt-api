import graphene
from flask import current_app

from app.appgraph.util import get_request_role_userid
from app import const
from app.services import projects


class PurgeProject(graphene.Mutation):
    """DO NOT USE. Purges project and all related objects from database."""

    class Arguments:
        project_id = graphene.UUID(required=False)
        project_name = graphene.String(required=False, description='Accepts an sql-style wildcard')

    deleted_projects = graphene.List(graphene.UUID)

    def mutate(self, info, project_id=None, project_name=None):
        role, user_id = get_request_role_userid(info)
        assert user_id, f'unauthenticated request'
        assert role == const.ROLE_ADMIN, f'{role} user cannot create projects'

        project_ids_list = projects.teardown(current_app.config, project_name=project_name, project_id=project_id)

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

        project_id = projects.setup_demo_project(current_app.config, name, req_user_id)

        return DemoProject(project_id=project_id)
