from app.cmd.testrun_status import testrun_status
from app.cmd.sentry import sentry_check
from app.cmd.tokens import job_token
from app.cmd.users import user_create, user_list_in_project


def register_commands(app):
    app.cli.add_command(sentry_check)
    app.cli.add_command(testrun_status)
    app.cli.add_command(job_token)
    app.cli.add_command(user_create)
    app.cli.add_command(user_list_in_project)
