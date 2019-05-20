# development server, enables flask commands
import cmds
from apps.bolt_api.app import create_app
from apps.bolt_metrics_api.app import exports


app = create_app()

cmds.register_commands(app)
exports.register_app(app)


if __name__ == '__main__':
    app.run('localhost', 5000, True, True)
