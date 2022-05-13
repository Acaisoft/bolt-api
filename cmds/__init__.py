import os

from .upload_file import upload_file
from . import users
from .projects import project_setup_demo, project_teardown
from .repositories import validate_repo
from .sentry import sentry_check
from .tokens import job_token, execution_data_export_token, project_data_export_token

if os.getenv('HTTP_DEBUG', False):
    # helpful for debugging client communication
    import logging
    import http.client as http_client

    http_client.HTTPConnection.debuglevel = 1

    # You must initialize logging, otherwise you'll not see debug output.
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


def register_commands(app):
    app.cli.add_command(sentry_check)
    app.cli.add_command(job_token)
    app.cli.add_command(execution_data_export_token)
    app.cli.add_command(project_data_export_token)
    app.cli.add_command(users.user_create)
    app.cli.add_command(users.user_list_in_project)
    app.cli.add_command(users.user_assign_role)
    app.cli.add_command(users.user_unassign)
    app.cli.add_command(users.user_create_invitation)
    app.cli.add_command(users.user_register)
    app.cli.add_command(users.disable_invitation)
    app.cli.add_command(users.user_login)
    app.cli.add_command(project_setup_demo)
    app.cli.add_command(project_teardown)
    app.cli.add_command(validate_repo)
    app.cli.add_command(upload_file)
