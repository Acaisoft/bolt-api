import numpy as np
from services.hasura import hce
from services import const


def _even_select(sample_size, target_size):
    if target_size > sample_size/2:
        cut = np.zeros(sample_size, dtype=int)
        q, r = divmod(sample_size, sample_size - target_size)
        indices = [q * i + min(i, r) for i in range(sample_size - target_size)]
        cut[indices] = False
    else:
        cut = np.ones(sample_size, dtype=int)
        q, r = divmod(sample_size, target_size)
        indices = [q * i + min(i, r) for i in range(target_size)]
        cut[indices] = True

    return cut


def _filter_points(data):
    metrics_data = data['execution_metrics_metadata'][0]['execution']['execution_metrics_data']
    metrics_data_len = len(metrics_data)
    point_selection_array = _even_select(metrics_data_len, const.MAX_GRAPH_POINTS)
    filtered_metrics_data = [point for point, not_select in zip(metrics_data, point_selection_array) if not not_select]

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
