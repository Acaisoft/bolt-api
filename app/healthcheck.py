from gql import gql
from healthcheck import HealthCheck, EnvironmentDump

from app.cache import get_cache
from upstream.devclient import devclient


def register_app(app):

    hc = HealthCheck(app, '/healthcheck')
    EnvironmentDump(app, '/env')

    def redis_up():
        info = get_cache(app.config).info()
        return True, 'ok'

    def hasura_up():
        # TODO: add endpoint to hasura migrations and call it here
        client = devclient(app.config)
        response = client.execute(gql('query { configuration { id } }'))
        assert response.get('configuration'), 'missing configuration'
        return True, 'ok'

    hc.add_check(redis_up)
    hc.add_check(hasura_up)

    return hc

