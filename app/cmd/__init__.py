from app.cmd.testrun_status import testrun_status
from app.cmd.sentry import sentry_check
from app.cmd.tokens import job_token


def register_commands(app):
    app.cli.add_command(sentry_check)
    app.cli.add_command(testrun_status)
    app.cli.add_command(job_token)
