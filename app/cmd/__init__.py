from app.cmd.sentry import sentry_check


def register_commands(app):
    app.cli.add_command(sentry_check)
