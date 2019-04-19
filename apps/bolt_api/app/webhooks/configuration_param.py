import math
from flask import Blueprint, request, jsonify, current_app

from services import const
from services.hasura import hce

bp = Blueprint('webhooks_configuration_param', __name__)


@bp.route('/update', methods=['POST'])
def configuration_param_update():
    event = request.get_json().get('event')
    assert event and event.get('op') == 'UPDATE', f'invalid event input: {str(event)}'

    old = event.get('data', {}).get('old')
    new = event.get('data', {}).get('new')

    if new.get('parameter_slug') == const.TESTPARAM_USERS and new.get('value') != old.get('value'):
        new_instances = math.ceil(int(new.get('value')) / const.TESTRUN_MAX_USERS_PER_INSTANCE)
        current_app.logger.info(f'updating configuration({new.get("configuration_id")}).instances to {new_instances}')
        # update instances in related configuration if number of users has changed
        resp = hce(current_app.config, '''mutation ($confId:uuid!, $numInstances:Int!) {
            update_configuration(_set:{instances:$numInstances}, where:{id:{_eq:$confId}}) { affected_rows }
        }''', {
            'confId': new.get('configuration_id'),
            'numInstances': new_instances,
        })
        assert resp['update_configuration'].get('affected_rows') is not None, f'unexpected error: {str(resp)}'

    return jsonify({})
