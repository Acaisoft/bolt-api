from datetime import datetime, timezone

from flask import Blueprint, jsonify, current_app

from apps.bolt_metrics_api.app import token
from services import exports
from services.logger import setup_custom_logger

logger = setup_custom_logger(__file__)

json_bp = Blueprint('exports.json', __name__)


@json_bp.route('/<string:request_token>/json', methods=['GET'])
def json(request_token):
    oid = token.verify(request_token)

    t_from = datetime.fromtimestamp(0).strftime('%Y-%m-%dT%H:%M:%S.%fz')
    t_to = datetime(year=4000, month=1, day=1).strftime('%Y-%m-%dT%H:%M:%S.%fz')

    data = exports.get_export_data(current_app.config, oid, t_from, t_to, exports.ALL_FIELDS)

    return jsonify(data)
