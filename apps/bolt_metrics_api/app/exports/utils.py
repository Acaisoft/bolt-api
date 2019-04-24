from datetime import datetime


def l2u(locust_timestamp:str) -> float:
    """
    Convert locust timestamp format to unix milisecond
    :param locust_timestamp: input timestamp in format: 2019-04-17T06:53:50.475089+00:00
    :return: float representing input in unix milisecond format
    """
    return datetime.strptime(
        locust_timestamp.replace('+00:00', '+0000'),
        '%Y-%m-%dT%H:%M:%S.%f%z'
    ).timestamp() * 1000


def fields_to_columns(fields_list):
    """
    Return a list of data field names parseable by grafana
    :param fields_list: ['field_a', 'field_b']
    :return: [{"text":"Field A","type":"number"},{"text":"Field B","type":"number"},]
    """
    def m(x:str):
        y = x.replace(':', ': ')
        return y.replace('_', ' ').title()

    def t(x):
        if x == 'timeserie:timestamp':
            return 'time'
        return 'number'

    return [{'text': m(f), 'type': t(f)} for f in fields_list]


def dataset_to_timeserie(dataset:dict, targets):
    """
    Convert locust testrun data to grafana/annotated timeserie format.
    Non-timeserie targets in @targets are ignored bc. locust limitations.
    :param dataset: data from db's execution table
    :param targets: fields to query on
    :return: jsonifiable ordered list of stucts
    """
    results_per_target = {}
    results = []

    for row in dataset.get('timeserie'):
        _ts = row.get('timestamp', None)
        if _ts is None:
            # get_export_data must include the timestamp column regardless of user spec
            raise RuntimeError('input data does not contain timestamp, unsuitable for timeserie')
        ts = l2u(_ts)
        for target in targets:
            metric, field = target.split(':')
            if target == 'timeserie:timestamp':
                continue
            if metric != 'timeserie':
                # Non-timeserie targets in @targets are ignored bc. locust limitations.
                continue
            if target not in results_per_target:
                results_per_target[target] = []
            results_per_target[target].append((float(row.get(field, 0)), ts))

    for k, v in results_per_target.items():
        results.append({
            'target': k,
            'datapoints': v
        })
    return results


def dataset_to_table(dataset:dict, targets):
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

        if metric in ('timeserie', 'errors'):
            # field is a raw column
            enumerable = enumerate(dataset[metric])
        elif metric == 'requests':
            # field is a json of lists of dicts and needs to be parsed deeper for actual fields
            enumerable = enumerate(dataset[metric][0]['request_result'])
        elif metric == 'distributions':
            # field is a json of lists of dicts and needs to be parsed deeper for actual fields
            enumerable = enumerate(dataset[metric][0]['distribution_result'])
        else:
            raise Exception(f'invalid metric category: {metric} in target {target}')

        for d_index, data_row in enumerable:
            if len(result_rows) <= d_index:
                result_rows.append(empty_row())
            value = data_row.get(field, None)
            if target == 'timeserie:timestamp':
                value = l2u(value)
            result_rows[d_index][t_index] = value

    return [{
        'type': 'table',
        'columns': fields_to_columns(targets),
        'rows': result_rows,
    }]
