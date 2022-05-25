# development server, enables flask commands
import cmds
from apps.bolt_api.app import create_app


app = create_app()

cmds.register_commands(app)


if __name__ == '__main__':
    app.run('localhost', 5000, True, True)
