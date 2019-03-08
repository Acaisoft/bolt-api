from flask import Blueprint, request, jsonify

from app.deployer.utils import get_test_run_status

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

    return jsonify({})
