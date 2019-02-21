import logging
import os

from gql import Client
from gql.transport.requests import RequestsHTTPTransport


_client = None


def devclient(config=None):
    global _client
    if not _client:
        # fallback to environment variables if app config is not specified
        if not config:
            config = os.environ

        target = config.get('HASURA_GQL', 'http://localhost:8080/v1alpha1/graphql')
        access_key = config.get('HASURA_GRAPHQL_ACCESS_KEY')
        assert access_key, 'HASURA_GRAPHQL_ACCESS_KEY is not set'
        logging.info(f'connecting hasura at {target} with access key:{bool(access_key)}')
        _client = Client(
            retries=0,
            transport=RequestsHTTPTransport(
                url=target,
                use_json=True,
                headers={'X-Hasura-Access-Key': access_key},
            )
        )
        logging.info('hasura connected')
    return _client
