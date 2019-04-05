import click
from flask import current_app
from flask.cli import with_appcontext
from app.services import projects


@click.command(name='project_setup_demo')
@click.argument('project_name', required=True)
@click.argument('user_id', required=True)
@with_appcontext
def project_setup_demo(project_name, user_id):
    """
    Create a project with two configurations and start it's tests.
    """
    projects.setup_demo_project(current_app.config, project_name, user_id)


@click.command(name='project_teardown')
@click.argument('project_name', required=False)
@click.argument('project_id', required=False)
@with_appcontext
def project_teardown(project_name, project_id):
    """
    Teardown a project by its name or its id.
    """
    projects.teardown(current_app.config, project_name, project_id)
