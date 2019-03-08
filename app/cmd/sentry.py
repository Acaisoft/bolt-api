import click
from flask import current_app
from flask.cli import with_appcontext


@click.command(name='sentry_check')
@with_appcontext
def sentry_check():
    sentry = current_app.extensions.get('sentry', None)
    if not sentry:
        raise AssertionError('SENTRY_DSN is not set')
    sentry.captureMessage("app started 2")
