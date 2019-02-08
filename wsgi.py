import os
from app import create_app


application = create_app()


def run_app():
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    run_app()
