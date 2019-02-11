from flask import Flask
from flask_graphql import GraphQLView

from app.appgraph import middleware
from app.appgraph import schema
from app.configure import configure


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    configure(app)

    app.add_url_rule('/graphql', view_func=GraphQLView.as_view(
        'graphql',
        schema=schema.AppSchema,
        graphiql=True,
        middleware=middleware.middleware_list,
    ))

    return app
