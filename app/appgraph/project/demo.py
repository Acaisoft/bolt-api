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
        role, user_id = get_request_role_userid(info, (const.ROLE_ADMIN,))

        project_ids_list = projects.teardown(current_app.config, project_name=project_name, project_id=project_id)

        return PurgeProject(deleted_projects=project_ids_list)


class DemoProject(graphene.Mutation):
    """DO NOT USE.
    Debug use only. Creates a complete project and starts two tests.
    Optionally creates a reader user in keycloak.
    """

    class Arguments:
        name = graphene.String()
        project_user_id = graphene.UUID(required=False)
        project_user_email = graphene.String(required=False)
        async = graphene.Boolean(required=False)

    project_id = graphene.UUID()

    def mutate(self, info, name, project_user_id=None, project_user_email=None, async=True):
        role, user_id = get_request_role_userid(info, (const.ROLE_ADMIN,))

        project_id = projects.setup_demo_project(current_app.config, name, str(project_user_id), project_user_email, async)

        return DemoProject(project_id=project_id)
