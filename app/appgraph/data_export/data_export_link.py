import graphene
from flask import current_app

from app.appgraph.util import get_request_role_userid, OutputValueFromFactory, OutputInterfaceFactory
from app import const
from app.services.exports.data_export_token import issue_export_token
from app.services.hasura import hce


class LinkReturnInterface(graphene.Interface):
    url = graphene.String()
    token = graphene.String()


class DataExportLink(graphene.Mutation):
    """Obtain execution data export url and a jwt."""

    class Arguments:
        execution_id = graphene.UUID(description='ID of execution to make public.')
        valid_hours = graphene.Int(description='How long the link remains valid.')

    Output = OutputInterfaceFactory(LinkReturnInterface, 'Delete')

    def mutate(self, info, execution_id, valid_hours):
        _, user_id = get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_MANAGER))

        token = issue_export_token(current_app.config, str(execution_id), user_id, valid_hours)

        return OutputValueFromFactory(DataExportLink, {'returning':[{
            'token': str(token),
            'url': f'/exports/graphana_simple_json/{str(token)}'
        }]})
