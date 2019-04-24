from services.exports import const
from services.hasura import hce


def fields_to_gql_aggregate(fields_list) -> str:
    # timeserie:timestamp must always be present, even if not returned
    fields = filter(lambda x: x.startswith('timeserie:') and x != 'timeserie:timestamp', fields_list)
    return ' '.join(map(lambda x: x.split(':')[1], fields))


def fields_to_gql_distribution(fields):
    out = []
    if list(filter(lambda x: x.startswith('requests:'), fields)):
        out.append('requests: result_distributions { request_result }')
    if list(filter(lambda x: x.startswith('distributions:'), fields)):
        out.append('distributions: result_distributions { distribution_result }')
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
                timeserie: result_aggregate (
                    order_by:{ timestamp:desc }
                    where:{ timestamp:{_lte:$t_to _gt:$t_from } }
                ) {
                    timestamp %(result_aggregate_fields)s
                }
                %(distribution_fields)s
                %(errors_fields)s
            }
        }''' % {
            'result_aggregate_fields': fields_to_gql_aggregate(fields_to_query),
            'distribution_fields': fields_to_gql_distribution(fields_to_query),
            'errors_fields': fields_to_gql_errors(fields_to_query),
        }, {
            't_from': t_from,
            't_to': t_to,
            'eid': oid[1],
        })
        return resp['execution'][0]
    else:
        # entire project
        resp = hce(config, '''query ($pid:uuid!, $t_from:timestamptz!, $t_to:timestamptz!) {
            execution (where:{
                configuration:{
                    project_id:{_eq:$pid}
                }
            }) {
                timeserie: result_aggregate (
                    order_by:{ timestamp:desc }
                    where:{ timestamp:{_lte:$t_to _gt:$t_from } }
                ) {
                    timestamp %(result_aggregate_fields)s
                }
                %(distribution_fields)s
                %(errors_fields)s
            }
        }''' % {
            'result_aggregate_fields': fields_to_gql_aggregate(fields_to_query),
            'distribution_fields': fields_to_gql_distribution(fields_to_query),
            'errors_fields': fields_to_gql_errors(fields_to_query),
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
                    dataset[g].extend(gg)

        return dataset