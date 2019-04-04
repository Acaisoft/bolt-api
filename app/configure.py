import logging
import os

from flask import Flask
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from app import const


def configure(app: Flask):
    conf_file_path = os.environ.get('CONFIG_FILE_PATH', 'localhost-config.py')
    app.config.from_pyfile(conf_file_path)

    secrets_file_path = os.environ.get('SECRETS_FILE_PATH', 'localhost-secrets.py')
    app.config.from_pyfile(secrets_file_path)

    sentry_dsn = app.config.get('SENTRY_DSN', None)
    if sentry_dsn and not app.debug:
        logging.info(f'sentry logging to {sentry_dsn.split("@")[-1]}')
        sentry_sdk.init(sentry_dsn, integrations=[FlaskIntegration()], release='v0.1.2')

    config_ver = app.config.get('CONFIG_VERSION', None)
    secrets_ver = app.config.get('SECRETS_VERSION', None)

    app.logger.info(f'app configured using {conf_file_path} v{config_ver} and {secrets_file_path} v{secrets_ver}')

    for handler in ('graphql.execution.executor', 'graphql.execution.utils'):
        ll = logging.getLogger(handler)
        if ll:
            ll.addFilter(IgnoreGraphQLErrors(debug=app.debug))

    validate(app)


def validate(app):
    missing = []
    for var_name in const.REQUIRED_CONFIG_VARS:
        if not app.config.get(var_name):
            missing.append(var_name)
    assert not missing, f'{len(missing)} undefined config variables: {", ".join(missing)}'
    app.logger.info('config valid')


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
