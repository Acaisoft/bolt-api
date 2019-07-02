from flask import Blueprint, request, jsonify, current_app
from schematics import types, models

from services.hasura import hce
from services.logger import setup_custom_logger


logger = setup_custom_logger(__file__)

bp = Blueprint('webhooks_execution_stage_log', __name__)


class Item(models.Model):
    name = types.StringType(required=True)
    status = types.StringType(required=True)


class Graph(models.Model):
    start = types.PolyModelType(Item, required=False)
    downloading_source = types.PolyModelType(Item, required=False)
    image_preparation = types.PolyModelType(Item, required=False)
    pre_start = types.PolyModelType(Item, required=False)
    monitoring = types.PolyModelType(Item, required=False)
    load_tests = types.PolyModelType(Item, required=False)
    clean_up = types.PolyModelType(Item, required=False)
    post_stop = types.PolyModelType(Item, required=False)
    finished = types.PolyModelType(Item, required=False)

    def init(self, graph):
        for g in graph:
            g.pop('type')
            self[g['name']] = Item(g)

    def to_json(self, has_load_tests, has_monitoring):
        graph = []
        if self.start:
            graph.append({'type': 'sequence', **self.start})
        if self.downloading_source:
            graph.append({'type': 'sequence', **self.downloading_source})
        if self.image_preparation:
            graph.append({'type': 'sequence', **self.image_preparation})
        if self.monitoring:
            graph.append({'type': 'parallel' if has_load_tests else 'sequence', **self.monitoring})
        if self.load_tests:
            graph.append({'type': 'parallel' if has_monitoring else 'sequence', **self.load_tests})
        if self.clean_up:
            graph.append({'type': 'sequence', **self.clean_up})
        if self.finished:
            graph.append({'type': 'sequence', **self.finished})
        logger.info(graph)
        return graph

    def update(self, status, stage):
        item = self[stage]
        if item is not None:
            item['status'] = status
            self[stage] = item
        else:
            new_item = Item()
            new_item['status'] = status
            new_item['name'] = stage
            self[stage] = new_item


@bp.route('/insert', methods=['POST'])
def execution_stage_log_insert():
    # future is not using already
    # TODO: delete code and migrations (triggers)
    return jsonify({})
    # data = request.get_json()
    # execution_stage_log = data['event']['data']['new']
    # execution_id = execution_stage_log['execution_id']
    # status = execution_stage_log['msg']
    # stage = execution_stage_log['stage']
    # execution_stage_graph_id, graph_data = get_execution_stage_graph(execution_id)
    # execution_data = get_execution(execution_id)
    # has_load_tests = execution_data['execution'][0]['configuration']['has_load_tests']
    # has_monitoring = execution_data['execution'][0]['configuration']['has_monitoring']
    # logger.info('------------------')
    # logger.info(f'{status} {stage}')
    # logger.info(f'{graph_data}')
    # logger.info('------------------')
    # model = Graph()
    # model.init(graph_data)
    # model.update(status, stage)
    # update_execution_stage_graph(execution_stage_graph_id, model.to_json(has_load_tests, has_monitoring))
    # return jsonify({})


def update_execution_stage_graph(_id, data):
    query = '''
        mutation ($id: Int, $data: json) {
            update_execution_stage_graph (where: {id:{_eq: $id}}, _set: {data: $data}){
                affected_rows
            }
        }
    '''
    response = hce(current_app.config, query, variable_values={'id': _id, 'data': data})
    return response['update_execution_stage_graph']['affected_rows']


def insert_empty_execution_stage_graph(execution_id):
    query  = '''
        mutation ($execution_id: uuid, $data: json) {
            insert_execution_stage_graph(objects: [{data: $data, execution_id: $execution_id}]) {
                returning {
                    id
                    data
                }
            }
        }
    '''
    response = hce(current_app.config, query, variable_values={'execution_id': execution_id, 'data': {}})
    return response


def get_execution_stage_graph(execution_id):
    query = '''
        query ($execution_id: uuid) {
            execution_stage_graph (where: {execution_id: {_eq: $execution_id}}){
                id
                data
            }
        }
    '''
    response = hce(current_app.config, query, variable_values={'execution_id': execution_id})
    try:
        return response['execution_stage_graph'][0]['id'], response['execution_stage_graph'][0]['data']
    except LookupError:
        new_graph = insert_empty_execution_stage_graph(execution_id)
        return new_graph['insert_execution_stage_graph']['returning'][0]['id'], new_graph['insert_execution_stage_graph']['returning'][0]['data']


def get_execution(execution_id):
    query = '''
        query ($execution_id: uuid) {
            execution (where: {id: {_eq: $execution_id}}){
                id
                configuration{
                    has_load_tests
                    has_monitoring
                }
            }
        }
    '''
    response = hce(current_app.config, query, variable_values={'execution_id': execution_id})
    return response
