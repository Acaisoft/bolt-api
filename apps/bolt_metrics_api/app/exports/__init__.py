from flask import request
from flask_limiter import Limiter

from apps.bolt_metrics_api.app.exports.graphana_simple_json import bp


def register_app(app):
    """
    These are publicly discoverable REST endpoints.
    """
    # enables grafana-specific endpoints, returns json of timeserie formatted rows
    # ratelimiting blueprint per url means each functionality's availability is equally distributed
    # among (token, method) where 1 token ~ 1 user, consider limiting per just the token
    limiter = Limiter(app, key_func=request_limiter)
    limiter.limit('100 per second')(bp)
    app.register_blueprint(bp, url_prefix='/exports/grafana_simple_json')


@bp.route('/')
def limited_gsj():
    return None


def request_limiter():
    return request.path
