from . import login


def register_app(app):
    """
    These registers auth pages
    """
    app.register_blueprint(login.bp, url_prefix='/auth')
