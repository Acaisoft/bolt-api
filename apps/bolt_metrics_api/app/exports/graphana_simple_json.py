from pprint import pprint
from flask import Blueprint, jsonify, request, current_app
from flask import abort

from apps.bolt_metrics_api.app.exports.utils import fields_to_columns, l2u
from services.logger import setup_custom_logger
from services.exports.verify_token import verify_token
from services.hasura import hce

logger = setup_custom_logger(__file__)

bp = Blueprint('graphana_simple_json', __name__)

queryable_fields = [
    'number_of_errors', 'number_of_fails', 'number_of_successes', 'number_of_users',
    'average_response_size', 'average_response_time',
]


def _verify(token):
    try:
        return verify_token(current_app.config, token)
    except Exception as e:
        logger.info('data export token validation failure: %s' % str(e))
        abort(404)


@bp.route('/<string:request_token>', methods=['GET'])
def datasource_test(request_token):
    """
    Present only to validate connection in Graphana config form.
    :param request_token: project data access token created by testrun_project_export
    :return:
    """
    logger.info('Testing data export endpoint')
    _verify(request_token)
    return jsonify({})


@bp.route('/<string:request_token>/search', methods=['POST'])
def search(request_token):
    _verify(request_token)
    return jsonify(queryable_fields)


@bp.route('/<string:request_token>/query', methods=['POST'])
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
    TODO: support mixed target types
    :param request_token: jwt token issued by exports.issue_export_token
    :return: graphable
    """

    oid = _verify(request_token)
    req = request.get_json()
    pprint(req)
    result_format = ''  # timeserie or table
    results_per_target = {}
    fields_to_query = []  # one of queryable_fields

    for i in req.get('targets'):
        f = i.get('target')
        if f:
            if f not in queryable_fields:
                abort(403)
            result_format = i.get('type', 'timeserie')
            fields_to_query.append(f)
            results_per_target[f] = []

    dataset = get_export_data(current_app.config, oid, req['range']['from'], req['range']['to'], fields_to_query)

    results = []
    if result_format == 'timeserie':
        for r in dataset:
            ts = l2u(r['timestamp'])
            for i in req.get('targets'):
                f = i.get('target')
                if f:
                    results_per_target[f].append((float(r.get(f, 0)), ts))
        for k, v in results_per_target.items():
            results.append({
                'target': k,
                'datapoints': v
            })
    elif result_format == 'table':
        result_rows = []
        for src_row in dataset:
            ts = l2u(src_row['timestamp'])
            table_row = [ts]
            for f in fields_to_query:
                table_row.append(float(src_row.get(f, 0)))
            result_rows.append(table_row)
        results = [{
            'type': 'table',
            'columns': fields_to_columns(fields_to_query),
            'rows': result_rows,
        }]

    return jsonify(results)


def get_export_data(config, oid, t_from, t_to, fields_to_query):
    # oid is a tuple of (project_id, execution_id), execution_id may be None, return all executions for project if so
    if oid[1]:
        # single execution
        resp = hce(config, '''query ($eid:uuid!, $t_from:timestamptz!, $t_to:timestamptz!) {
            execution {
                result_aggregate (
                    order_by:{timestamp:desc}
                    where:{
                        id:{_eq:$eid}
                        timestamp:{
                            _lte:$t_to
                            _gt:$t_from
                        }
                    }) {
                    timestamp %(fields)s
                }
            }
        }''' % {'fields': ' '.join(fields_to_query)}, {
            't_from': t_from,
            't_to': t_to,
            'eid': oid[1],
        })
        return resp['execution'][0]['result_aggregate']
    else:
        # entire project
        resp = hce(config, '''query ($pid:uuid!, $t_from:timestamptz!, $t_to:timestamptz!) {
            execution (where:{
                configuration:{
                    project_id:{_eq:$pid}
                }
            }) {
                result_aggregate (
                    order_by:{timestamp:desc}
                    where:{
                        timestamp:{
                            _lte:$t_to
                            _gt:$t_from
                        }
                    }) {
                    timestamp %(fields)s
                }
            }
        }''' % {'fields': ' '.join(fields_to_query)}, {
            't_from': t_from,
            't_to': t_to,
            'pid': oid[0],
        })
        # concatenate each execution's results
        dataset = []
        for e in resp['execution']:
            dataset.extend(e['result_aggregate'])
        sorted(dataset, key=lambda x: x['timestamp'])
        return dataset



@bp.route('/<string:request_token>/annotations', methods=['POST'])
def annotations(request_token):
    eid = _verify(request_token)
    # TODO: click through to get actual example query
    return jsonify({})


@bp.route('/<string:request_token>/tag-keys', methods=['POST'])
def tag_keys(request_token):
    # appears not used
    eid = _verify(request_token)
    pprint(request.get_json())
    return jsonify({})


@bp.route('/<string:request_token>/tag-values', methods=['POST'])
def tag_values(request_token):
    # appears not used
    eid = _verify(request_token)
    pprint(request.get_json())
    return jsonify({})
