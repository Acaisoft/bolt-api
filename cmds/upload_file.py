import os
import time
from subprocess import getoutput

import click

from flask import current_app
from flask.cli import with_appcontext

from services.uploads.get_upload_url import get_upload_url
from services.uploads.upload_processor import register_upload_processor

from services.logger import setup_custom_logger

logger = setup_custom_logger(__name__)


@click.command(name='upload_file')
@click.option('--path', required=True, help='absolute file path')
@with_appcontext
def upload_file(path):
    """
    Uploads a file to GCS.
    """
    # register upload processor
    register_upload_processor(current_app.config)

    if not os.path.exists(path):
        logger.error(f'file "{path}" does not exist')
        return

    base64md5 = getoutput(f'cat {path} | openssl dgst -md5 -binary  | openssl enc -base64')
    mime_type = getoutput(f'file --mime-type {path}').rsplit(': ')[1]
    upload_url = request_upload_token(current_app.config, path)

    cmd = f'curl -v -X PUT -H "Content-Type: {mime_type}" -H "Content-MD5: {base64md5}" -T - "{upload_url}" < {path}'
    logger.info(f'executing: {cmd}')
    r = getoutput(cmd)
    # print(r)

    while True:
        logger.debug('sleeping')
        time.sleep(10)


def request_upload_token(config, path):
    # crude but effective, for testing/debugging only
    base64md5 = getoutput(f'cat {path} | openssl dgst -md5 -binary  | openssl enc -base64')
    mime_type = getoutput(f'file --mime-type {path}').rsplit(': ')[1]
    upload_url, download_url = get_upload_url(config, base64md5, mime_type)
    return upload_url
