from app.services.deployer.routes import bp
from app.services.deployer.clients import client


def register_app(app):
    if app.debug:
        app.register_blueprint(bp)
