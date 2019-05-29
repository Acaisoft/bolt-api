from flask import request, jsonify, current_app
from flask_limiter import Limiter

from apps.bolt_metrics_api.app import token
from apps.bolt_metrics_api.app.exports.graphana_simple_json import grafana_bp
from apps.bolt_metrics_api.app.exports.json import json_bp


def register_app(app):
    """
    These are publicly discoverable REST endpoints.
    """
    # enables grafana-specific endpoints, returns json of timeserie formatted rows
    # ratelimiting blueprint per url means each functionality's availability is equally distributed
    # among (token, method) where 1 token ~ 1 user, consider limiting per just the token
    limiter = Limiter(app, key_func=request_limiter)
    limiter.limit('100 per second')(grafana_bp)
    limiter.limit('5 per second')(json_bp)
    app.register_blueprint(grafana_bp, url_prefix='/exports')
    app.register_blueprint(json_bp, url_prefix='/exports')


@grafana_bp.route('/<string:request_token>')
def exports_index(request_token):
    if not current_app.debug:
        token.verify(request_token)
    return jsonify({'available_views': {
        f'{request.base_url}/': 'this page',
        f'{request.base_url}/json': 'timeseries raw data output',
        f'{request.base_url}/grafana': 'grafana connectivity test endpoint',
        f'{request.base_url}/grafana/search': 'available metrics list',
        f'{request.base_url}/grafana/query': 'filterable data output',
    }})


def request_limiter():
    return request.path
