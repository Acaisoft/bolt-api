from flask import Flask
from flask_graphql import GraphQLView

from app.appgraph import middleware
from app.appgraph import schema


def create_app(test_config=None):
    app = Flask(__name__)

    app.add_url_rule('/graphql', view_func=GraphQLView.as_view(
        'graphql',
        schema=schema.AppSchema,
        graphiql=True,
        middleware=middleware.middleware_list,
    ))

    return app
