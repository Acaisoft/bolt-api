import json

import graphene
from flask import current_app

from app import const
from app.appgraph.users import types
from app.appgraph.util import get_request_role_userid
from app.services.user_management import user_management
from app.cache import get_cache


class UserList(graphene.ObjectType):
    testrun_user_list = graphene.Field(
        types.UserListInterface,
        description='Return a list of users in a project.',
        project_id=graphene.UUID(description='Project id to list users of.')
    )

    def resolve_testrun_user_list(self, info, project_id):
        req_role, user_id = get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_MANAGER))

        project_id = str(project_id)
        c = get_cache(current_app.config)
        cn = f'resolve_testrun_user_list_{project_id}'
        users = c.get(cn)
        if not users:
            users = user_management.list_users_in_project(project_id)
            c.set(cn, json.dumps(users), 60)
        else:
            users = json.loads(users)

        users_response = [types.UserListItemType(**x) for x in users]
        return types.UserListType(project_id=project_id, users=users_response)
