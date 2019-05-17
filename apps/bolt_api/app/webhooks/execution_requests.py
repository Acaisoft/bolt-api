from flask import Blueprint, request, jsonify, current_app

from apps.bolt_api.app.webhooks.execution_request_totals import update_execution_request_totals
from services.cache import get_cache
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

    logger.info('computing execution request totals')

    new = event.get('data', {}).get('new')
    logger.info(f'new entry {new}')

    if not should_upsert(new):
        logger.info('not upserting execution request totals, key is older')
        return jsonify({})

    err = upsert(new)
    if err is not None:
        logger.error(f'error inserting execution request totals on execution: {str(err)}')
        return jsonify({})

    err = update_execution_request_totals(new['execution_id'], req_identifier=new['identifier'])
    if err is not None:
        logger.error(f'error updating request totals on execution: {str(err)}')

    return jsonify({})


def should_upsert(data: dict) -> bool:
    key = f'{data["execution_id"]}_{data["identifier"]}'
    cache = get_cache(current_app)
    entry = cache.get(key)
    if not entry or data['id'] > int(entry):
        logger.info(f'should_upsert execution request totals is TRUE, {data["id"]} > {str(entry)}')
        cache.set(key, data['id'], ex=60 * 60)
        return True
    logger.info(f'should_upsert execution request totals is False, {data["id"]} < {str(entry)}')
    return False


def upsert(data: dict):
    del data['id']

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
        'data': data,
    })

    return totals_response.get('errors', None)
