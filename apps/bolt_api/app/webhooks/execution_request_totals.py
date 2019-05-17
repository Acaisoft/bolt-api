from flask import current_app

from services.hasura import hce
from services.logger import setup_custom_logger

logger = setup_custom_logger(__file__)


def update_execution_request_totals(execution_id: str, req_identifier: str):
    """
    Updates execution and execution_totals with numbers of requests and failures from results tables.
    :param execution_id:
    :param req_identifier: request identifier, per locust return type
    :return:
    """
    response = hce(current_app.config, '''query ($execution_id:uuid!, $identifier:String!) {
        execution_request_totals_aggregate(where:{execution_id:{_eq:$execution_id}}){
            aggregate {
                sum {num_requests}
                sum {num_failures}
                sum {requests_per_second}
                avg {average_response_time}
                min {min_response_time}
                max {max_response_time}
            }
        }

        execution_requests_aggregate(where:{
            execution_id:{ _eq:$execution_id }
            identifier:{ _eq:$identifier }
        }){
            aggregate {
                min {average_content_size}
                max {average_content_size}
            }
        }
    }''', variable_values={
        'execution_id': execution_id,
        'identifier': req_identifier,
    })
    err = response.get('errors', None)
    if err is not None:
        logger.error(f'error calculating request totals on execution: {str(err)}')
        return err

    aggs = response['execution_request_totals_aggregate']['aggregate']
    total = aggs['sum']['num_requests']
    fails = aggs['sum']['num_failures']
    max_content_size = response['execution_requests_aggregate']['aggregate']['max']['average_content_size']
    min_content_size = response['execution_requests_aggregate']['aggregate']['min']['average_content_size']

    if total is not None or fails is not None:
        response = hce(current_app.config, '''mutation (
            $identifier:String!,
            $execution_id:uuid!, 
            $total_requests:Int!, 
            $passed_requests:Int!, 
            $failed_requests:Int!,
            $max_content_size:numeric!,
            $min_content_size:numeric!,
        ) {
            update_execution(
                where:{id:{_eq:$execution_id}}
                _set:{
                    total_requests: $total_requests
                    passed_requests: $passed_requests
                    failed_requests: $failed_requests
                }
            ) { affected_rows }

            update_execution_request_totals(
                where:{
                    execution_id:{ _eq:$execution_id }
                    identifier:{ _eq:$identifier }
                }
                _set:{
                    max_content_size: $max_content_size
                    min_content_size: $min_content_size
                }
            ) { affected_rows }

        }''', variable_values={
            'execution_id': execution_id,
            'identifier': req_identifier,
            'total_requests': total,
            'failed_requests': fails,
            'passed_requests': int(total) - int(fails),
            'max_content_size': max_content_size,
            'min_content_size': min_content_size,
        })
        return response.get('errors', None)
