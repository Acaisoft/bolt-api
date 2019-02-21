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
        response = client.execute(gql('query { configuration { id } }'))
        assert response.get('configuration'), 'missing configuration'
        return True, 'ok'

    def deployer_up():
        response = deployer.clients.healthcheck(app.config).health_check_get()
        assert response.status == 'healthy'
        return True, 'ok'

    hc.add_check(redis_up)
    hc.add_check(hasura_up)
    hc.add_check(deployer_up)

    return hc
