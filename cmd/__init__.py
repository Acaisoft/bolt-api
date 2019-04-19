from cmd import users
from cmd.projects import project_setup_demo, project_teardown
from cmd.repositories import validate_repo
from cmd.sentry import sentry_check
from cmd.testrun_status import testrun_status
from cmd.tokens import job_token, execution_data_export_token, project_data_export_token


def register_commands(app):
    app.cli.add_command(sentry_check)
    app.cli.add_command(testrun_status)
    app.cli.add_command(job_token)
    app.cli.add_command(execution_data_export_token)
    app.cli.add_command(project_data_export_token)
    app.cli.add_command(users.user_create)
    app.cli.add_command(users.user_list_in_project)
    app.cli.add_command(users.user_assign_role)
    app.cli.add_command(users.user_unassign)
    app.cli.add_command(project_setup_demo)
    app.cli.add_command(project_teardown)
    app.cli.add_command(validate_repo)
