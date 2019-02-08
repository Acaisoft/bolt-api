import logging
import os

from gql import Client
from gql.transport.requests import RequestsHTTPTransport


def devclient():
    target = os.environ.get('HASURA_GQL', 'http://localhost:8080/v1alpha1/graphql')
    logging.info("connecting hasura at ", target)
    return Client(
        retries=0,
        transport=RequestsHTTPTransport(
            url=target,
            use_json=True
        )
    )
