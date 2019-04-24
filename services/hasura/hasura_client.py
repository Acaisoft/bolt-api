import os

import requests
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from graphql import print_ast
from graphql.execution import ExecutionResult

from services import const

_client = None


class VerboseHTTPTransport(RequestsHTTPTransport):
    # RequestsHTTPTransport hides error messages for statuses in 400-range, this copypasta returns them instead

    def execute(self, document, variable_values=None, timeout=None):
        query_str = print_ast(document)
        payload = {
            'query': query_str,
            'variables': variable_values or {}
        }

        data_key = 'json' if self.use_json else 'data'
        post_args = {
            'headers': self.headers,
            'auth': self.auth,
            'timeout': timeout or self.default_timeout,
            data_key: payload
        }
        request = requests.post(self.url, **post_args)

        if request.status_code >= 500:
            request.raise_for_status()

        result = request.json()
        assert 'errors' in result or 'data' in result, 'Received non-compatible response "{}"'.format(result)
        return ExecutionResult(
            errors=result.get('errors'),
            data=result.get('data')
        )


def hasura_client(config=None):
    global _client
    if not _client:
        # fallback to environment variables if app config is not specified
        if not config:
            config = os.environ

        target = config.get('HASURA_GQL')
        assert target, 'HASURA_GQL is not set'
        access_key = config.get('HASURA_GRAPHQL_ACCESS_KEY')
        assert access_key, 'HASURA_GRAPHQL_ACCESS_KEY is not set'

        _client = Client(
            retries=0,
            transport=VerboseHTTPTransport(
                url=target,
                use_json=True,
                headers={
                    'X-Hasura-Access-Key': access_key,
                    'X-Hasura-User-Id': const.HASURA_CLIENT_USER_ID,
                    'X-Hasura-Role': 'admin',
                },
            )
        )
    return _client


def hce(config, query, *args, **kwargs):
    if type(query) is str:
        if config.get('HCE_DEBUG', False):
            print(query)
        query = gql(query)
    return hasura_client(config).execute(query, *args, **kwargs)
