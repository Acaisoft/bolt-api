import click
from flask.cli import with_appcontext
from app.auth import user_management


@click.command(name='user_create')
@click.argument('email', required=True)
@click.argument('project', required=True)
@click.argument('role', required=True)
@with_appcontext
def user_create(email, project, role):
    """
    Create a user in keycloak with given roles
    """
    user_management.user_create(email, project, role)
