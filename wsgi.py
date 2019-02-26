from app import create_app


application = create_app()


def run_app():
    application.run(host='0.0.0.0', debug=True, port=application.config.get('PORT'))


if __name__ == '__main__':
    run_app()
