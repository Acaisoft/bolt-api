from flask import Blueprint, jsonify, request, current_app
from flask import abort

from apps.bolt_metrics_api.app import token
from services import exports
from services.exports.data_extractor import l2u, fields_to_columns
from services.logger import setup_custom_logger

logger = setup_custom_logger(__file__)

grafana_bp = Blueprint('exports.grafana_simple_json', __name__)


@grafana_bp.route('/<string:request_token>/grafana', methods=['GET'])
def datasource_test(request_token):
    """
    Present only to validate connection in Grafana config form.
    :param request_token: project data access token created by testrun_project_export
    :return:
    """
    logger.info('Testing data export endpoint')
    token.verify(request_token)
    return jsonify({})


@grafana_bp.route('/<string:request_token>/grafana/search', methods=['POST'])
def search(request_token):
    token.verify(request_token)
    return jsonify(exports.ALL_FIELDS)


@grafana_bp.route('/<string:request_token>/grafana/query', methods=['POST'])
def query(request_token):
    """
    Example request body:
        {'adhocFilters': [],
         'dashboardId': 1,
         'interval': '100ms',
         'intervalMs': 100,
         'maxDataPoints': 523,
         'panelId': 8,
         'range': {'from': '2019-04-17T06:53:47.724Z',
                   'raw': {'from': '2019-04-17T06:53:47.724Z',
                           'to': '2019-04-17T06:54:30.257Z'},
                   'to': '2019-04-17T06:54:30.257Z'},
         'rangeRaw': {'from': '2019-04-17T06:53:47.724Z',
                      'to': '2019-04-17T06:54:30.257Z'},
         'scopedVars': {'__interval': {'text': '100ms', 'value': '100ms'},
                        '__interval_ms': {'text': 100, 'value': 100}},
         'targets': [{'refId': 'A', 'target': 'number_of_users', 'type': 'timeserie'},
                     {'refId': 'B',
                      'target': 'average_response_time',
                      'type': 'table'}],
         'timezone': 'browser'}
    :param request_token: jwt token issued by exports.issue_export_token
    :return: graphable
    """

    oid = token.verify(request_token)
    req = request.get_json()
    results_per_target = {}
    targets = []
    table_targets = []
    timeseries_targets = []

    for i in req.get('targets'):
        f = i.get('target')
        if f:
            if f not in exports.ALL_FIELDS:
                logger.warn(f'invalid field in requested targets: "{f}"')
                abort(403)
            result_format = i.get('type', 'timeserie')
            results_per_target[f] = []
            targets.append(f)
            if result_format == 'timeserie':
                timeseries_targets.append(f)
            elif result_format == 'table':
                table_targets.append(f)

    dataset = exports.get_export_data(current_app.config, oid, req['range']['from'], req['range']['to'], targets)

    results = []
    if timeseries_targets:
        results.extend(dataset_to_timeserie(dataset, timeseries_targets))
    if table_targets:
        results.extend(dataset_to_table(dataset, table_targets))

    return jsonify(results)


@grafana_bp.route('/<string:request_token>/grafana/annotations', methods=['POST'])
def annotations(request_token):
    eid = token.verify(request_token)
    # TODO: click through to get actual example query
    return jsonify({})


@grafana_bp.route('/<string:request_token>/grafana/tag-keys', methods=['POST'])
def tag_keys(request_token):
    # appears not used
    eid = token.verify(request_token)
    return jsonify({})


@grafana_bp.route('/<string:request_token>/grafana/tag-values', methods=['POST'])
def tag_values(request_token):
    # appears not used
    eid = token.verify(request_token)
    return jsonify({})


def dataset_to_timeserie(dataset: dict, targets):
    """
    Convert locust testrun data to grafana/annotated timeserie format.
    Non-timeserie targets in @targets are ignored bc. locust limitations.
    :param dataset: data from db's execution table
    :param targets: fields to query on
    :return: jsonifiable ordered list of stucts
    """
    results_per_target = {}
    results = []

    for target in targets:
        metric, field = target.split(':')
        for row in dataset.get(metric):
            # get the timestamp
            ts = row.get('timestamp', None)
            if ts is None:
                # get_export_data must include the timestamp column regardless of user spec
                raise RuntimeError('input data does not contain timestamp, unsuitable for timeserie')

            if type(ts) != float:
                ts = l2u(ts)

            # get identifier for a sub-target, if present
            result_target = target
            if metric in ('distributions', 'requests', 'errors'):
                subtarget = row.get('name', None)
                if subtarget:
                    result_target = f'{metric}:{field}:{subtarget}'

            if result_target not in results_per_target:
                results_per_target[result_target] = []

            value = row.get(field, '')
            try:
                value = float(value)
            except:
                pass
            results_per_target[result_target].append((value, ts))

    for k, v in results_per_target.items():
        results.append({
            'target': k,
            'datapoints': v
        })
    return results


def dataset_to_table(dataset: dict, targets):
    """
    Example dataset combining different categories of metrics
    {'timeserie': [],
    'requests': [],
    'errors': [
        {'name': '/'}, {'name': '/random'}, {'name': '/send'}, {'name': '/echo/hello'},
        {'name': '/error/400or500'}, {'name': '/error/401'}, {'name': '/error/404'},
        {'name': '/echo/hello'}, {'name': '/'}, {'name': '/send'}, {'name': '/error/404'},
    ]}
    """

    def empty_row():
        return [0 for i in range(len(targets))]

    result_rows = []
    for t_index, target in enumerate(targets):
        metric, field = target.split(':')
        for d_index, data_row in enumerate(dataset[metric]):
            if len(result_rows) <= d_index:
                result_rows.append(empty_row())
            value = data_row.get(field, None)
            if target.endswith(':timestamp'):
                if type(value) != float:
                    value = l2u(value)
            result_rows[d_index][t_index] = value

    return [{
        'type': 'table',
        'columns': fields_to_columns(targets),
        'rows': result_rows,
    }]
