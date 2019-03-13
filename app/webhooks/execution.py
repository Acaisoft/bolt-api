from flask import Blueprint, request, jsonify, current_app
from gql import gql

from app import const
from app.deployer.utils import get_test_run_status
from bolt_api.upstream.devclient import devclient

bp = Blueprint('webhooks', __name__)


@bp.route('/execution/update', methods=['POST'])
def execution_update():
    event = request.get_json().get('event')
    assert event and event.get('op') == 'UPDATE', f'invalid event input: {str(event)}'

    old = event.get('data', {}).get('old')
    new = event.get('data', {}).get('new')

    if new.get('status') != old.get('status'):
        # execution has entered running phase through locust-wrapper, fetch job info once, in case user hasn't had chance
        output = get_test_run_status(new.get('id'))

    if new.get('status') == const.TESTRUN_FINISHED:
        # mark as performed successfully
        resp = devclient(current_app.config).execute(gql('''mutation ($confId:uuid!) {
            update_configuration(_set:{performed:true}, where:{id:{_eq:$confId}}) { affected_rows }
        }'''), {'confId': new.get('configuration_id')})
        assert resp['update_configuration'].get('affected_rows') is not None, f'unexpected error: {str(resp)}'

    return jsonify({})