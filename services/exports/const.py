# summary of available metrics and associated fields

groups = ['timeserie', 'requests', 'distributions', 'errors', 'nfs']

aggregate_fields = [
    'timeserie:timestamp',
    'timeserie:number_of_errors',
    'timeserie:number_of_fails',
    'timeserie:number_of_successes',
    'timeserie:number_of_users',
    'timeserie:average_response_size',
    'timeserie:average_response_time',
]

errors_fields = [
    'errors:timestamp',
    'errors:identifier',
    'errors:method',
    'errors:name',
    'errors:exception_data',
    'errors:number_of_occurrences'
]

distributions_fields = [
    'distributions:timestamp',
    'distributions:identifier',
    'distributions:method',
    'distributions:name',
    'distributions:num_requests',
    'distributions:p50',
    'distributions:p66',
    'distributions:p75',
    'distributions:p80',
    'distributions:p90',
    'distributions:p95',
    'distributions:p98',
    'distributions:p99',
    'distributions:p100',
]

requests_fields = [
    'requests:timestamp',
    'requests:identifier',
    'requests:method',
    'requests:name',
    'requests:num_requests',
    'requests:num_failures',
    'requests:median_response_time',
    'requests:average_response_time',
    'requests:min_response_time',
    'requests:max_response_time',
    'requests:average_content_size',
    'requests:requests_per_second',
]

# fields populated through extensions, currently only NFS is supported
# example db format: {"1557306759.9596684":{"total_savings":99.94,"write_throughput":64.87,"compression":0.13,"read_throughput":0,"current_bytes":226013151232,"dedupe":99.94,"current_files":22694},}
nfs_fields = [
    'nfs:timestamp',
    'nfs:total_savings',
    'nfs:write_throughput',
    'nfs:read_throughput',
    'nfs:compression',
    'nfs:current_bytes',
    'nfs:dedupe',
    'nfs:current_files',
]

ALL_FIELDS = aggregate_fields + errors_fields + distributions_fields + requests_fields + nfs_fields

field_types = {
    'nfs:timestamp': 'time',
    'errors:timestamp': 'time',
    'errors:method': 'string',
    'errors:name': 'string',
    'errors:exception_data': 'string',
    'distributions:timestamp': 'time',
    'distributions:method': 'string',
    'distributions:name': 'string',
    'requests:timestamp': 'time',
    'requests:method': 'string',
    'requests:name': 'string',
}
