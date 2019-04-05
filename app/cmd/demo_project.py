import click
from flask.cli import with_appcontext
from app.services import demo


@click.command(name='setup_demo_project')
@click.argument('project_name', required=True)
@click.argument('user_id', required=True)
@with_appcontext
def setup_demo_project(project_name, user_id):
    """
    Create a project with two configurations and start it's tests.
    """
    demo.setup_demo_project(project_name, user_id)
