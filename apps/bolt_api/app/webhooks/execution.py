from flask import Blueprint, request, jsonify, current_app

from apps.bolt_api.app.webhooks.execution_request_totals import update_execution_request_totals
from services import const
from services.deployer.utils import get_test_run_status
from services.hasura import hce

bp = Blueprint('webhooks_execution', __name__)


@bp.route('/update', methods=['POST'])
def execution_update():
    req_body = request.get_json()
    event = req_body.get('event')
    assert event and event.get('op') == 'UPDATE', f'invalid event input: {str(event)}'

    old = event.get('data', {}).get('old')
    new = event.get('data', {}).get('new')

    if new.get('status') != old.get('status'):
        # execution has entered running phase through locust-wrapper, fetch job info once, in case user hasn't had chance
        output = get_test_run_status(new.get('id'))

    if new.get('status') == const.TESTRUN_FINISHED:
        # mark as performed successfully
        resp = hce(current_app.config, '''mutation ($confId:uuid!) {
            update_configuration(_set:{performed:true}, where:{id:{_eq:$confId}}) { affected_rows }
            update_test_creator(where:{test_sources:{configurations:{id:{_eq:$confId}}}}, _set:{performed:true}) { affected_rows }
            update_repository(where:{test_sources:{configurations:{id:{_eq:$confId}}}}, _set:{performed:true}) { affected_rows }
        }''', {'confId': new.get('configuration_id')})
        assert resp['update_configuration'].get('affected_rows') is not None, f'unexpected error: {str(resp)}'
        # update execution totals
        update_execution_request_totals(new.get('id'))

    return jsonify({})
