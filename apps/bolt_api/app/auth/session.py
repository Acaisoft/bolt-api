from flask import Blueprint, request, make_response
from werkzeug.exceptions import Unauthorized

from services.logger import setup_custom_logger

logger = setup_custom_logger(__file__)
bp = Blueprint('auth-session', __name__)


@bp.route('/session', methods=['GET'])
def session():
    token = request.cookies.get('AUTH_TOKEN', False)
    if not token:
        return Unauthorized('Missing AUTH_TOKEN cookie')

    response = make_response({'AUTH_TOKEN': token})
    response.set_cookie('AUTH_TOKEN', expires=0)

    return response
