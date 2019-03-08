import logging

from flask import Flask

from app import healthcheck, graphql, deployer, cmd
from app.auth import auth
from app.cache import get_cache
from app.configure import configure
from bolt_api.upstream.devclient import devclient


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

    ## initialize cache and hasura clients
    get_cache(app.config)
    devclient(app.config)

    cmd.register_commands(app)

    logging.info('application ready')
    return app
