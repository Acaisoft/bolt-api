import logging
import os

from flask import Flask
from flask.logging import default_handler
from logging.config import dictConfig


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

    config_ver = app.config.get('CONFIG_VERSION', None)
    secrets_ver = app.config.get('SECRETS_VERSION', None)

    logging.info(f'app configured using {conf_file_path} v{config_ver} and {secrets_file_path} v{secrets_ver}')
