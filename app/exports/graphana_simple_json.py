from flask import Blueprint, jsonify, request, current_app
from flask import abort

from app.logger import setup_custom_logger
from app.services.exports.verify_token import verify_token

logger = setup_custom_logger(__file__)

bp = Blueprint('graphana_simple_json', __name__)


def _verify(token):
    try:
        return verify_token(current_app.config, token)
    except Exception as e:
        logger.info('data export token validation failure: %s' % str(e))
        abort(404)


@bp.route('/<string:request_token>', methods=['GET'])
def datasource_test(request_token):
    """
    Present only to validate connection in Graphana config form.
    :param request_token: project data access token created by testrun_project_export
    :return:
    """
    logger.info('Testing data export endpoint')
    eid = _verify(request_token)
    return jsonify({})


@bp.route('/<string:request_token>/search', methods=['POST'])
def search(request_token):

    eid = _verify(request_token)
    return jsonify({})


@bp.route('/<string:request_token>/query', methods=['POST'])
def query(request_token):

    eid = _verify(request_token)
    return jsonify({})


@bp.route('/<string:request_token>/annotations', methods=['POST'])
def annotations(request_token):

    eid = _verify(request_token)
    return jsonify({})


@bp.route('/<string:request_token>/tag-keys', methods=['POST'])
def tag_keys(request_token):

    eid = _verify(request_token)
    return jsonify({})


@bp.route('/<string:request_token>/tag-values', methods=['POST'])
def tag_values(request_token):

    eid = _verify(request_token)
    return jsonify({})



@bp.route('/<string:request_token>/ss', methods=['POST'])
def datasource(request_token):

    eid = _verify(request_token)

    if request.method == 'GET':
        return jsonify([{}])
    elif request.method == 'POST':
        req = request.get_json()
        return jsonify([{
            'annotations': req.get('annotation')
        }])