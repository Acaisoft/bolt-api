import logging
import os

from flask import Flask
import sentry_sdk
from sentry_sdk.integrations.flask import \
    FlaskIntegration


def configure(app: Flask):
    conf_file_path = os.environ.get('CONFIG_FILE_PATH', 'localhost-config.py')
    app.config.from_pyfile(conf_file_path)

    secrets_file_path = os.environ.get('SECRETS_FILE_PATH', 'localhost-secrets.py')
    app.config.from_pyfile(secrets_file_path)

    sentry_dsn = app.config.get('SENTRY_DSN', None)
    if sentry_dsn:
        logging.info(f'sentry logging to {sentry_dsn.split("@")[-1]}')
        sentry_sdk.init(sentry_dsn, integrations=[FlaskIntegration()], release='v0.1.2')

    config_ver = app.config.get('CONFIG_VERSION', None)
    secrets_ver = app.config.get('SECRETS_VERSION', None)

    logging.info(f'app configured using {conf_file_path} v{config_ver} and {secrets_file_path} v{secrets_ver}')
