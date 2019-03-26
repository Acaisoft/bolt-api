from . import execution


def register_app(app):
    app.register_blueprint(execution.bp, url_prefix='/webhooks/execution')
