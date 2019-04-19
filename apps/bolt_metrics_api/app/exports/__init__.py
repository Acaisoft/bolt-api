from apps.bolt_metrics_api.app.exports import graphana_simple_json


def register_app(app):
    """
    These are publicly discoverable REST endpoints.
    """
    app.register_blueprint(graphana_simple_json.bp, url_prefix='/exports/graphana_simple_json')
