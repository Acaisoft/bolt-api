# development server, enables flask commands
import cmd
from apps.bolt_api.app import create_app


application = create_app()

cmd.register_commands(application)


def run_app():
    port = application.config.get('PORT')
    application.logger.info(f'listening on port {port}')
    application.run(host='0.0.0.0', debug=True, port=port, threaded=True)


if __name__ == '__main__':
    run_app()
