import click
from flask import current_app
from flask.cli import with_appcontext

from services.validators import validate_accessibility


@click.command(name='validate_repo')
@click.argument('repository_url', required=True)
@with_appcontext
def validate_repo(repository_url):
    resp = validate_accessibility(current_app.config, repository_url)
    print(resp)
