from flask import Flask

from app import healthcheck, graphql
from app.auth import auth
from app.configure import configure
from bolt_api.upstream.devclient import devclient


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    configure(app)

    if test_config:
        app.config.from_object(test_config)

    ## configure hasura upstream client
    devclient(app.config)

    ## this app's graphs
    graphql.register_app(app)

    ## authorization endpoints
    auth.register_app(app)

    ## healthchecks
    healthcheck.register_app(app)

    return app
