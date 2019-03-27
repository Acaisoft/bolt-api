from flask import Flask

from app import healthcheck, graphql, deployer, cmd, webhooks
from app.auth import auth
from app.cache import get_cache
from app.configure import configure
from app.hasura_client import hasura_client


def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=True)

    configure(app)

    if test_config:
        app.config.from_object(test_config)

    ## this app's graphs
    graphql.register_app(app)

    ## authorization endpoints
    auth.register_app(app)

    ## deployer service
    deployer.register_app(app)

    ## healthchecks
    healthcheck.register_app(app)

    ## webhooks
    webhooks.register_app(app)

    ## initialize cache and hasura clients
    get_cache(app.config)
    hasura_client(app.config)

    cmd.register_commands(app)

    app.logger.info('application ready')
    return app
