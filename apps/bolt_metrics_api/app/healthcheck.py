from healthcheck import HealthCheck, EnvironmentDump

from services.hasura import hasura_client, hce


def register_app(app):

    hc = HealthCheck(app, '/healthcheck')

    if app.debug:
        EnvironmentDump(app, '/env')

    def hasura_up():
        client = hasura_client(app.config)
        try:
            response = hce(app.config, 'query { user_project { id } }')
        except Exception as e:
            return False, str(e)
        if not response.get('user_project', None):
            return False, 'missing root tables'
        return True, 'ok'

    hc.add_check(hasura_up)

    return hc
