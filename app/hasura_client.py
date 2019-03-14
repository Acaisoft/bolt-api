import logging
import os

import requests
from gql import Client
from gql.transport.requests import RequestsHTTPTransport
from graphql import print_ast
from graphql.execution import ExecutionResult

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

        if 400 <= request.status_code < 500:
            pass
        else:
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

        target = config.get('HASURA_GQL', 'http://localhost:8080/v1alpha1/graphql')
        access_key = config.get('HASURA_GRAPHQL_ACCESS_KEY')
        assert access_key, 'HASURA_GRAPHQL_ACCESS_KEY is not set'
        logging.info(f'connecting hasura at {target} with access key:{bool(access_key)}')
        _client = Client(
            retries=0,
            transport=VerboseHTTPTransport(
                url=target,
                use_json=True,
                headers={'X-Hasura-Access-Key': access_key},
            )
        )
        logging.info('hasura connected')
    return _client
