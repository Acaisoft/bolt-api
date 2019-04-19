# development server, enables flask commands
from flask import Flask

import cmd
from services import const
from services.configure import configure, validate


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    configure(app)
    validate(app, const.REQUIRED_BOLT_API_CONFIG_VARS)

    cmd.register_commands(app)

    return app


application = create_app()
