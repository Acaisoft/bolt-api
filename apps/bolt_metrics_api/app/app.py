from flask import Flask, request, jsonify
from flask_limiter import Limiter

from apps.bolt_metrics_api.app import exports, healthcheck
from services.configure import configure, validate
from services.logger import setup_custom_logger
from services import const
from services.cache import get_cache
from services.hasura import hasura_client


logger = setup_custom_logger(__name__)


def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=True)

    configure(app)
    validate(app, const.REQUIRED_METRICS_API_CONFIG_VARS)

    if test_config:
        app.config.from_object(test_config)

    validate(app, const.REQUIRED_METRICS_API_CONFIG_VARS)

    ## initialize cache and hasura clients
    get_cache(app.config, app)
    hasura_client(app.config)

    ## public REST apis
    exports.register_app(app)

    ## healthchecks
    healthcheck.register_app(app)

    logger.info('application ready')
    return app
