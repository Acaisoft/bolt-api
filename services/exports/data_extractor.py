import json
from datetime import datetime

from services.exports import const
from services.hasura import hce

GQL_TIMESTAMP = 'order_by:{ timestamp:desc } where:{ timestamp:{_lte:$t_to _gt:$t_from } }'
GQL_CREATED_AT = 'order_by:{ created_at:desc } where:{ slug:{_eq:"dynamically-stats"} }'


def targets_to_fields(targets_list, metric) -> str:
    # timeserie:timestamp must always be present, even if not returned
    fields = filter(lambda x: x.startswith(metric + ':') and ':timestamp' not in x, targets_list)
    return ' '.join(map(lambda x: x.split(':')[1], fields))


def fields_to_gql(fields):
    out = []

    if list(filter(lambda x: x.startswith('timeserie:'), fields)):
        out.append('timeserie: result_aggregate ( %(GQL_TIMESTAMP)s ) { timestamp %(fields)s }' % {
            'GQL_TIMESTAMP': GQL_TIMESTAMP,
            'fields': targets_to_fields(fields, 'timeserie'),
        })

    if list(filter(lambda x: x.startswith('requests:'), fields)):
        out.append('requests: execution_requests ( %(GQL_TIMESTAMP)s ) { timestamp identifier name %(fields)s }' % {
            'GQL_TIMESTAMP': GQL_TIMESTAMP,
            'fields': targets_to_fields(fields, 'requests'),
        })

    if list(filter(lambda x: x.startswith('distributions:'), fields)):
        out.append(
            'distributions: execution_distributions ( %(GQL_TIMESTAMP)s ) { timestamp identifier name %(fields)s }' % {
                'GQL_TIMESTAMP': GQL_TIMESTAMP,
                'fields': targets_to_fields(fields, 'distributions'),
            })

    if list(filter(lambda x: x.startswith('errors:'), fields)):
        out.append('errors: execution_errors ( %(GQL_TIMESTAMP)s ) { timestamp identifier name %(fields)s }' % {
            'GQL_TIMESTAMP': GQL_TIMESTAMP,
            'fields': targets_to_fields(fields, 'errors'),
        })

    if list(filter(lambda x: x.startswith('nfs:'), fields)):
        # extensions hold their timestamps and details in a single json which has to be manually decoded later
        out.append('nfs: execution_additional_data ( %(GQL_CREATED_AT)s ) { data }' % {
            'GQL_CREATED_AT': GQL_CREATED_AT,
        })

    return ' '.join(out)


def fields_to_gql_errors(fields):
    error_columns = list(filter(lambda x: x.startswith('errors:'), fields))
    if error_columns:
        return 'errors: result_errors { %s }' % ' '.join(map(lambda x: x.split(':')[1], error_columns))
    return ''


def get_export_data(config, oid, t_from, t_to, fields_to_query):
    # oid is a tuple of (project_id, execution_id), execution_id may be None, return all executions for project if so
    if oid[1]:
        # single execution
        resp = hce(config, '''query ($eid:uuid!, $t_from:timestamptz!, $t_to:timestamptz!) {
            execution (where:{id:{_eq:$eid}}) {
                %(timeserie_fields)s
            }
        }''' % {
            'timeserie_fields': fields_to_gql(fields_to_query),
        }, {
                       't_from': t_from,
                       't_to': t_to,
                       'eid': oid[1],
                   })
        print(json.dumps(resp))
        return resp['execution'][0]
    else:
        # entire project
        resp = hce(config, '''query ($pid:uuid!, $t_from:timestamptz!, $t_to:timestamptz!) {
            execution (where:{
                configuration:{
                    project_id:{_eq:$pid}
                }
            }) {
                %(timeserie_fields)s
            }
        }''' % {
            'timeserie_fields': fields_to_gql(fields_to_query),
        }, {
                       't_from': t_from,
                       't_to': t_to,
                       'pid': oid[0],
                   })

        # concatenate each execution's results
        dataset = dict((g, []) for g in const.groups)
        for e in resp['execution']:
            for g in const.groups:
                gg = e.get(g)
                if gg:
                    if g == 'nfs':
                        gg = convert_data(g, gg)
                    dataset[g].extend(gg)

        return dataset


def convert_data(group, rows):
    return rows


def l2u(locust_timestamp: str) -> float:
    """
    Convert locust timestamp format to unix milisecond
    :param locust_timestamp: input timestamp in format: 2019-04-17T06:53:50.475089+00:00
    :return: float representing input in unix milisecond format
    """
    try:
        return datetime.strptime(
            locust_timestamp.replace('+00:00', '+0000'),
            '%Y-%m-%dT%H:%M:%S%z'
        ).timestamp() * 1000
    except:
        try:
            return datetime.strptime(
                locust_timestamp.replace('+00:00', '+0000'),
                '%Y-%m-%dT%H:%M:%S.%f%z'
            ).timestamp() * 1000
        except:
            return datetime.strptime(
                locust_timestamp,
                '%Y-%m-%dT%H:%M:%S%z'
            ).timestamp() * 1000


def fields_to_columns(fields_list):
    """
    Return a list of data field names parseable by grafana
    :param fields_list: ['field_a', 'field_b']
    :return: [{"text":"Field A","type":"number"},{"text":"Field B","type":"number"},]
    """

    def m(x: str):
        y = x.replace(':', ': ')
        return y.replace('_', ' ').title()

    def t(x: str):
        return const.field_types.get(x, 'number')

    return [{'text': m(f), 'type': t(f)} for f in fields_list]
