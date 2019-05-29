import graphene
from flask import current_app

from services import const, gql_util
from services.exports.data_export_token import issue_export_token


class LinkReturnInterface(graphene.Interface):
    token = graphene.String()
    grafana_url = graphene.String()
    raw_json = graphene.String()


class DataExportLink(graphene.Mutation):
    """Obtain execution data export url and a jwt."""

    class Arguments:
        execution_id = graphene.UUID(description='ID of execution to make public.')
        valid_hours = graphene.Int(description='How long the link remains valid.')

    Output = gql_util.OutputInterfaceFactory(LinkReturnInterface, 'Delete')

    def mutate(self, info, execution_id, valid_hours):
        _, user_id = gql_util.get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_TENANT_ADMIN, const.ROLE_MANAGER))

        token = issue_export_token(current_app.config, const.EXPORT_SCOPE_EXECUTION, str(execution_id), user_id, valid_hours)

        # TODO: fix host
        return gql_util.OutputValueFromFactory(DataExportLink, {'returning': [{
            'token': str(token),
            'raw_json': f'https://api-metrics.dev.bolt.acaisoft.io/exports/{str(token)}/json',
            'grafana_url': f'https://api-metrics.dev.bolt.acaisoft.io/exports/{str(token)}/grafana',
        }]})
