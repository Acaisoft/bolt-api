import click
import sentry_sdk
from flask.cli import with_appcontext


@click.command(name='sentry_check')
@with_appcontext
def sentry_check():
    sentry_sdk.capture_message("test sentry message")
