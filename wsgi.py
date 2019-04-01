from app import create_app


application = create_app()


def run_app():
    port = application.config.get('PORT')
    application.logger.info(f'listening on port {port}')
    application.run(host='0.0.0.0', debug=True, port=port)


if __name__ == '__main__':
    run_app()
