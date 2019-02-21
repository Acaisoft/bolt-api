from flask_graphql import GraphQLView
from app.appgraph import middleware
from app.appgraph import schema


def register_app(app):
    ## graphql queries for hasura to be a remote for
    app.add_url_rule('/graphql', view_func=GraphQLView.as_view(
        'graphql',
        schema=schema.AppSchema,
        graphiql=True,
        middleware=middleware.middleware_list,
    ))
