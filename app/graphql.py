from flask import Flask
from flask_graphql import GraphQLView

from app.appgraph import schema


def register_app(app:Flask):
    ## graphql queries for hasura to be a remote for
    app.add_url_rule('/graphql', view_func=GraphQLView.as_view(
        'graphql',
        schema=schema.AppSchema,
        graphiql=True,
    ))
