from gql import gql
from healthcheck import HealthCheck, EnvironmentDump

from app import deployer
from app.cache import get_cache
from bolt_api.upstream.devclient import devclient


def register_app(app):

    hc = HealthCheck(app, '/healthcheck')
    EnvironmentDump(app, '/env')

    def redis_up():
        info = get_cache(app.config).info()
        return True, 'ok'

    def hasura_up():
        client = devclient(app.config)
        try:
            response = client.execute(gql('query { user { id } }'))
        except Exception as e:
            return False, str(e)
        if not response.get('user', None):
            return False, 'missing root tables'
        return True, 'ok'

    def deployer_up():
        try:
            response = deployer.clients.healthcheck(app.config).health_check_get()
        except Exception as e:
            return False, str(e)
        if response.status != 'healthy':
            return False, f'deployer is not healthy, it is {response.status}'
        return True, 'ok'

    hc.add_check(redis_up)
    # hc.add_check(hasura_up)
    hc.add_check(deployer_up)

    return hc
