from . import execution
from . import configuration_param


def register_app(app):
    """
    These register private callbacks for hasura to push events to. Must be private.
    """
    app.register_blueprint(execution.bp, url_prefix='/webhooks/execution')
    app.register_blueprint(configuration_param.bp, url_prefix='/webhooks/configuration_param')
