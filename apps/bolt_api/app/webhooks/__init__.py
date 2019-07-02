from . import execution
from . import configuration_param
from . import execution_stage_log


def register_app(app):
    """
    These register private callbacks for hasura to push events to. Must be private.
    """
    app.register_blueprint(execution.bp, url_prefix='/webhooks/execution')
    app.register_blueprint(configuration_param.bp, url_prefix='/webhooks/configuration_param')
    app.register_blueprint(execution_stage_log.bp, url_prefix='/webhooks/execution_stage_log')
