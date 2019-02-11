import graphene
from flask import current_app


class OauthInterface(graphene.Interface):
    provider = graphene.String()
    client_id = graphene.String()


class Oauth(graphene.ObjectType):
    class Meta:
        interfaces = (OauthInterface,)


class QueryOauth(graphene.ObjectType):
    oauth_confs = graphene.List(OauthInterface)

    def resolve_oauth_confs(self, info):
        conf = current_app().config
        return [
            Oauth(
                provider='Google',
                client_id=conf.get('GOOGLE_CLIENT_ID'),
            ),
            Oauth(
                provider='GitHub',
                client_id=conf.get('GITHUB_CLIENT_ID'),
            ),
        ]
