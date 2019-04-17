from flask import Flask

from app import healthcheck, cmd, webhooks, appgraph, exports
from app.logger import setup_custom_logger
from app.services import deployer
from app.cache import get_cache
from app.configure import configure
from app.services.hasura import hasura_client


logger = setup_custom_logger(__name__)


def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=True)

    configure(app)

    if test_config:
        app.config.from_object(test_config)

    ## this app's graphs
    appgraph.register_app(app)
    ## and public REST apis
    exports.register_app(app)

    ## deployer service
    deployer.register_app(app)

    ## healthchecks
    healthcheck.register_app(app)

    ## webhooks
    webhooks.register_app(app)

    ## initialize cache and hasura clients
    get_cache(app.config, app)
    hasura_client(app.config)

    cmd.register_commands(app)

    logger.info('application ready')
    return app
