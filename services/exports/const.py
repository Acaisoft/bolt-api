# summary of available metrics and associated fields

groups = ['timeserie', 'requests', 'distributions', 'errors']

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