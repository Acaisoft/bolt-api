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
    'errors:error_type',
    'errors:name',
    'errors:exception_data',
    'errors:number_of_occurrences'
]

distributions_fields = [
    # these map to json fields in execution.result_distributions.request_result column
    'requests:Min response time',
    'requests:# failures',
    'requests:Max response time',
    'requests:Name',
    'requests:Median response time',
    'requests:Average Content Size',
    'requests:Average response time',
    'requests:Method',
    'requests:Requests/s',
    'requests:# requests',

    # these map to json fields in execution.result_distributions.distribution_result column
    'distributions:Name',
    'distributions:# requests',
    'distributions:99%',
    'distributions:75%',
    'distributions:66%',
    'distributions:98%',
    'distributions:100%',
    'distributions:50%',
    'distributions:80%',
    'distributions:90%',
    'distributions:95%'
]