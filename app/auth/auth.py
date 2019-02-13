from authlib.flask.client import OAuth
from flask import Flask, jsonify, current_app
from loginpass import create_flask_blueprint, Google, GitHub
from app.auth.hasura import hasura_token_for_user
from app.cache import get_cache


_authlib: OAuth = None


def get_authlib():
    return _authlib


def handle_authorize(remote, token, user_info):
    if not user_info:
        return '<h2>unauthorized</h2>'

    email = user_info['email']

    if not email and remote.OAUTH_NAME == GitHub.OAUTH_NAME:
        # github email requires additional step
        if not remote.token and token:
            remote.token = token
        resp = remote.get('https://api.github.com/user/emails')
        if resp.ok:
            for i in resp.json():
                if i['primary'] and i['verified'] and i['email']:
                    email = i['email']
                    break

    if not email:
        return '<h2>user unauthorized</h2>'

    return hasura_token_for_user(current_app.config, email)


def register_oauth(app: Flask):
    global _authlib
    _authlib = OAuth(app, get_cache(app.config))

    auth_google = create_flask_blueprint(Google, _authlib, handle_authorize)
    auth_github = create_flask_blueprint(GitHub, _authlib, handle_authorize)

    if app.debug:

        @app.route('/')
        def index():
            return '<ul><li><a href="/google/login">Login with Google</a></li>' \
                   '<li><a href="/github/login">or with GitHub</a></li></ul>'

        app.register_blueprint(auth_google, url_prefix='/google')
        app.register_blueprint(auth_github, url_prefix='/github')
