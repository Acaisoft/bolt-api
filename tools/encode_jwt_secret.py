# takes jwt signing secret key from flask app and encodes it for use in Hasura
# expects "SECRET_KEY" key in ../instance/conf.py
import json

from app import create_app, const


def do():
    app = create_app()
    app.config.from_pyfile('conf.py')
    return {
        "type": app.config.get(const.JWT_ALGORITHM),
        "key": app.config.get(const.SECRET_KEY),
    }


if __name__ == '__main__':
    print(json.dumps(do()))
