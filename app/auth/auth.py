from authlib.flask.client import OAuth
from flask import Flask
from loginpass import create_flask_blueprint, Google, GitHub
from app.auth.hasura import hasura_token_for_user


# TODO: replace with redis
class Cache(object):
    def __init__(self):
        self._data = {}

    def get(self, k):
        return self._data.get(k)

    def set(self, k, v, timeout=None):
        self._data[k] = v

    def delete(self, k):
        if k in self._data:
            del self._data[k]


def register_oauth(app: Flask):
    oauth = OAuth(app, Cache())

    @app.route('/')
    def index():
        return '<ul><li><a href="/google/login">Login with Google</a></li>' \
               '<li><a href="/github/login">or with GitHub</a></li></ul>'

    @app.route('/')
    def index():
        return '<ul><li><a href="/google/login">Login with Google</a></li>' \
               '<li><a href="/github/login">or with GitHub</a></li></ul>'

    def handle_authorize(remote, token, user_info):
        if not user_info:
            return '<h2>unauthorized</h2>'

        email = user_info['email']

        if not email and remote.OAUTH_NAME == GitHub.OAUTH_NAME:
            # github email requires additional step
            resp = remote.get('https://api.github.com/user/emails')
            if resp.ok:
                for i in resp.json():
                    if i['primary'] and i['verified'] and i['email']:
                        email = i['email']
                        break

        if not email:
            return '<h2>user unauthorized</h2>'

        return hasura_token_for_user(app.config, email)

    ggbp = create_flask_blueprint(Google, oauth, handle_authorize)
    app.register_blueprint(ggbp, url_prefix='/google')

    ghbp = create_flask_blueprint(GitHub, oauth, handle_authorize)
    app.register_blueprint(ghbp, url_prefix='/github')
