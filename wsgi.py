# development server, enables flask commands
import cmd
from apps.bolt_api.app import create_app
from apps.bolt_metrics_api.app import exports


app = create_app()

cmd.register_commands(app)
exports.register_app(app)


if __name__ == '__main__':
    app.run('localhost', 5005, True, True)
