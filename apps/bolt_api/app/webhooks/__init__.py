from flask import request, jsonify, current_app
from flask_limiter import Limiter

from . import execution
from . import configuration_param
from . import execution_requests


def register_app(app):
    """
    These register private callbacks for hasura to push events to. Must be private.
    """
    limiter = Limiter(app, key_func=request_limiter)
    limiter.limit('10 per second')(execution.bp)
    limiter.limit('2 per second')(configuration_param.bp)
    limiter.limit('2 per second')(execution_requests.bp)
    app.register_blueprint(execution.bp, url_prefix='/webhooks/execution')
    app.register_blueprint(configuration_param.bp, url_prefix='/webhooks/configuration_param')
    app.register_blueprint(execution_requests.bp, url_prefix='/webhooks/execution_requests')


def request_limiter():
    return request.path
