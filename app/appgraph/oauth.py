import graphene
from flask import current_app
from app.auth.auth import handle_authorize, get_authlib


class OauthInterface(graphene.Interface):
    provider = graphene.String()
    client_id = graphene.String()


class Oauth(graphene.ObjectType):
    class Meta:
        interfaces = (OauthInterface,)


class OauthAuthtokenInterface(graphene.Interface):
    jwt_token = graphene.String()


class OauthAuthtoken(graphene.ObjectType):
    class Meta:
        interfaces = (OauthAuthtokenInterface,)


class QueryOauth(graphene.ObjectType):
    oauth_conf = graphene.List(OauthInterface, name='oauth_conf')
    oauth_authtoken = graphene.Field(
        OauthAuthtokenInterface,
        name="oauth_authtoken",
        required=False,
        provider=graphene.String(),
        state=graphene.String(),
        code=graphene.String(),
    )

    def resolve_oauth_conf(self, info):
        conf = current_app.config
        providers = [
            Oauth(
                provider='Google',
                client_id=conf.get('GOOGLE_CLIENT_ID'),
            ),
            Oauth(
                provider='GitHub',
                client_id=conf.get('GITHUB_CLIENT_ID'),
            ),
        ]
        if conf.debug:
            providers.append(Oauth(
                provider='DevServer',
                client_id=conf.get('DEVSERVER_CLIENT_ID'),
            ))
        return providers

    def resolve_oauth_authtoken(self, info, provider, state, code):
        provider = provider.lower()
        remote = get_authlib()._clients.get(provider)
        params = {
            'code': code,
            'state': state,
        }
        redirect_uri = '{}/{}/auth'.format(current_app.config.get('OAUTH_REDIRECT'), provider)
        token = remote.fetch_access_token(redirect_uri, **params)
        user_info = remote.profile(token=token)
        jwt_token = handle_authorize(remote, token, user_info)
        return OauthAuthtoken(jwt_token=str(jwt_token))
