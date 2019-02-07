from gql import Client
from gql.transport.requests import RequestsHTTPTransport


def devclient():
    return Client(
        retries=0,
        transport=RequestsHTTPTransport(
            url='http://localhost:8080/v1alpha1/graphql',
            use_json=True
        )
    )