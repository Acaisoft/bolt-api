import graphene
import json

from flask import current_app
from services import gql_util
from services.hasura import hce
from apps.bolt_api.app.appgraph.argo.parser import ArgoFlowParser


class ExecutionLogInterface(graphene.Interface):
    data = graphene.JSONString()
    argo_id = graphene.String()


class CreateExecutionLog(graphene.Mutation):

    class Arguments:
        data = graphene.JSONString()
        argo_id = graphene.String()

    Output = gql_util.OutputInterfaceFactory(ExecutionLogInterface, 'Create')

    @staticmethod
    def validate(argo_id):
        assert type(argo_id) is str, f'argo_id must be string'

    def mutate(self, info, data, argo_id):
        CreateExecutionLog.validate(argo_id)
        query = '''
            mutation ($data: json, $argo_id: String) {
                insert_argo_execution_log (objects: [{data: $data, argo_id: $argo_id}]){
                    affected_rows
                }
            }
        '''
        if type(data) is str:
            data = json.loads(data)
        hce(current_app.config, query, variable_values={'data': data, 'argo_id': argo_id})
        parser = ArgoFlowParser(argo_id=argo_id)
        parser.parse_argo_statuses(data)
        return gql_util.OutputValueFromFactory(CreateExecutionLog, {'returning': [{}]})
