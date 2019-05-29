from flask import current_app, abort

from services.exports import verify_token
from services.logger import setup_custom_logger

logger = setup_custom_logger(__file__)


def verify(token):
    try:
        return verify_token(current_app.config, token)
    except Exception as e:
        logger.info('data export token validation failure: %s' % str(e))
        abort(404)
