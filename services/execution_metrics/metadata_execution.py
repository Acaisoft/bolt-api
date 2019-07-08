from math import ceil
from services.hasura import hce
from services import const


def _even_select(sequence, num):
    length = len(sequence)
    if length > num:
        return [sequence[int(ceil(i * length / num))] for i in range(num)]
    else:
        return sequence


def _filter_points(data):
    metrics_data = data['execution_metrics_metadata'][0]['execution']['execution_metrics_data']
    filtered_metrics_data = _even_select(metrics_data, const.MAX_GRAPH_POINTS)
    return filtered_metrics_data


def get_executions_by_execution_id(config, execution_id):
    query = '''query ($eid: uuid!) {
      execution_metrics_metadata(where: {execution_id: {_eq: $eid}}) {
        execution {
          execution_metrics_data(order_by: {timestamp: asc}) {
            data
          }
        }
      }
    }
    '''

    query_params = {'eid': str(execution_id),}

    resp = hce(config,  query, query_params)

    metrics_data = _filter_points(resp)

    return metrics_data


def get_executions_by_execution_id_by_timestamp(config, execution_id, start, end):
    query = '''query ($eid: uuid!, $start: timestamptz!, $end: timestamptz!) {
      execution_metrics_metadata(where: {execution_id: {_eq: $eid}}) {
        execution {
          execution_metrics_data(order_by: {timestamp: asc}, where: {timestamp: {_gte: $start, _lte: $end}}) {
            data
          }
        }
      }
    }
    '''

    query_params = {
        'eid': str(execution_id),
        'start': str(start),
        'end': str(end),
    }

    resp = hce(config, query, query_params)

    metrics_data = _filter_points(resp)

    return metrics_data
