from flask import Blueprint, request, jsonify, current_app

from services.hasura import hce
from services.logger import setup_custom_logger

logger = setup_custom_logger(__file__)

bp = Blueprint('webhooks_execution_requests', __name__)


@bp.route('/insert', methods=['POST'])
def update_execution_requests_stats_totals():
    event = request.get_json().get('event')

    if event.get('op') != 'INSERT':
        # do not calculate on DELETE as hasura will send an event for each row of a deleted table
        return jsonify({})

    new = event.get('data', {}).get('new')
    del new['id']
    execution_id = new['execution_id']
    req_identifier = new['identifier']

    totals_response = hce(current_app.config, '''mutation ($data:[execution_request_totals_insert_input!]!) {
        insert_execution_request_totals(
            objects: $data,
            on_conflict: {
                constraint: execution_request_totals_pkey
                update_columns: [
                    average_content_size, average_response_time, max_response_time, median_response_time, 
                    min_response_time, num_failures, num_requests, requests_per_second, timestamp
                ]
            }
        ) { affected_rows }
    }''', variable_values={
        'data': new,
    })
    err = totals_response.get('errors', None)
    if err is not None:
        logger.warn(f'error inserting execution request totals on execution: {str(err)}')
        return jsonify({})

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
        logger.warn(f'error calculating request totals on execution: {str(err)}')
        return jsonify({})

    aggs = response['execution_request_totals_aggregate']['aggregate']
    total = int(aggs['sum']['num_requests']) + int(new['num_requests'])
    fails = int(aggs['sum']['num_failures']) + int(new['num_failures'])
    max_content_size = response['execution_requests_aggregate']['aggregate']['max']['average_content_size']
    min_content_size = response['execution_requests_aggregate']['aggregate']['min']['average_content_size']

    if total is not None and fails is not None:
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
        err = response.get('errors', None)
        if err is not None:
            logger.warn(f'error updating request totals on execution: {str(err)}')

    return jsonify({})
