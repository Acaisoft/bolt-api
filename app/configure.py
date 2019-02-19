import os

from flask import Flask
from flask.logging import default_handler
from logging.config import dictConfig

from app.cache import get_cache


def configure(app: Flask):
    app.logger.removeHandler(default_handler)

    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
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

    get_cache(app.config)
