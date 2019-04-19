from services.deployer.routes import bp


def register_app(app):
    if app.debug:
        app.register_blueprint(bp)
