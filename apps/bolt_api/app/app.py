import logging

from flask import Flask

from apps.bolt_api.app import appgraph, healthcheck, webhooks
from services.configure import configure, validate
from services.logger import setup_custom_logger
from services import deployer, const, uploads
from services.cache import get_cache
from services.hasura import hasura_client


logger = setup_custom_logger(__name__)


def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=True)

    configure(app)

    if app.config.get('DEBUG_SERVER') is not None:
        import pydevd_pycharm
        pydevd_pycharm.settrace(
            app.config.get('DEBUG_SERVER'),
            port=app.config.get('DEBUG_PORT', 6060),
            stdoutToServer=True,
            stderrToServer=True
        )

    for handler in ('graphql.execution.executor', 'graphql.execution.utils'):
        ll = logging.getLogger(handler)
        if ll:
            ll.addFilter(IgnoreGraphQLErrors(debug=app.debug))

    if test_config:
        app.config.from_object(test_config)

    validate(app, const.REQUIRED_BOLT_API_CONFIG_VARS)

    ## initialize cache and hasura clients
    get_cache(app.config, app)
    hasura_client(app.config)

    ## this app's graphs
    appgraph.register_app(app)

    ## deployer service
    deployer.register_app(app)

    ## healthchecks
    healthcheck.register_app(app)

    ## webhooks
    webhooks.register_app(app)

    logger.info('application ready')
    return app


class IgnoreGraphQLErrors(logging.Filter):
    """
    python-graphene logs every intercepted exception twice with loglevel EXCEPTION, which gets picked up by Sentry.
    This silences these logs unless we're in debug mode.
    """
    debug = False

    def __init__(self, name='', debug=False):
        self.debug = debug
        super().__init__(name)

    def filter(self, record:logging.LogRecord):
        if record:
            if record.exc_info and record.exc_info[0] is AssertionError and not self.debug:
                return 0
            if 'graphql.error.located_error.GraphQLLocatedError' in record.getMessage():
                return 0
        return 1

