from healthcheck import HealthCheck, EnvironmentDump

from services.cache import get_cache
from services.hasura import hasura_client, hce


def register_app(app):

    hc = HealthCheck(app, '/healthcheck')

    if app.debug:
        EnvironmentDump(app, '/env')

    def redis_up():
        info = get_cache(app.config).info()
        return True, 'ok'

    def hasura_up():
        client = hasura_client(app.config)
        try:
            response = hce(app.config, 'query { user { id } }')
        except Exception as e:
            return False, str(e)
        if not response.get('user', None):
            return False, 'missing root tables'
        return True, 'ok'

    hc.add_check(redis_up)
    hc.add_check(hasura_up)

    return hc
