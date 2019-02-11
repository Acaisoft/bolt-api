import logging
import os

from gql import Client
from gql.transport.requests import RequestsHTTPTransport


_client = None


def devclient():
    global _client
    if not _client:
        target = os.environ.get('HASURA_GQL', 'http://localhost:8080/v1alpha1/graphql')
        logging.info("connecting hasura at %s", target)
        _client = Client(
            retries=0,
            transport=RequestsHTTPTransport(
                url=target,
                use_json=True
            )
        )
    return _client
