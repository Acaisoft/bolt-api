import logging
import os
import time
from logging.config import dictConfig

from flask import Flask
from flask.logging import default_handler
from raven.contrib.flask import Sentry


def configure(app: Flask):
    app.logger.removeHandler(default_handler)

    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] [%(levelname)s in %(module)s] %(message)s',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }},
        'root': {
            'level': 'INFO',
            'handlers': ['wsgi']
        }
    })

    conf_file_path = os.environ.get('CONFIG_FILE_PATH', 'localhost-config.py')
    app.config.from_pyfile(conf_file_path)

    secrets_file_path = os.environ.get('SECRETS_FILE_PATH', 'localhost-secrets.py')
    app.config.from_pyfile(secrets_file_path)

    sentry_dsn = app.config.get('SENTRY_DSN', None)
    if sentry_dsn and not app.debug:
        logging.info(f'sentry logging to {sentry_dsn.split("@")[-1]}')
        if not app.config.get('SENTRY_CONFIG'):
            app.config['SENTRY_CONFIG'] = {}
        app.config['SENTRY_CONFIG']['release'] = 'v0.1'
        Sentry(app, dsn=sentry_dsn, level=logging.WARNING)

    config_ver = app.config.get('CONFIG_VERSION', None)
    secrets_ver = app.config.get('SECRETS_VERSION', None)

    logging.info(f'app configured using {conf_file_path} v{config_ver} and {secrets_file_path} v{secrets_ver}')
