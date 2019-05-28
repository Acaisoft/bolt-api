import json
import unittest

import requests
import vcr
from werkzeug.test import Client
from werkzeug.wrappers import Response

from apps.bolt_api.wsgi import application
from services import const


class BoltResponse(Response):
    """
    Helper for parsing graphql responses.
    """

    def json(self):
        return json.loads(self.data)

    def errors(self):
        return self.json().get('errors', None)

    def one(self, query_name):
        """helper returning first entry from 'repsonse.data.<query_name>.returning' """
        return self.returning(query_name)[0]

    def returning(self, query_name):
        """helper returning contents from 'repsonse.data.<query_name>.returning[0]' """
        return self.json()['data'][query_name]['returning']


class BoltCase(unittest.TestCase):
    """
    Testcase with vcr and custom graphql client.
    To record responses Hasura must be up and running in development mode.
    """

    def setUp(self) -> None:
        super(BoltCase, self).setUp()
        # setup flask client
        self.client = Client(application=application, response_wrapper=BoltResponse)
        # setup vcr context manager
        self.vcr_cassette_name = f'{self.__class__.__name__}.{self._testMethodName}.yaml'
        _vcr = vcr.VCR(
            serializer='json',
            cassette_library_dir='fixtures',
            record_mode='once',
            match_on=['uri', 'method', 'raw_body'],
        ).use_cassette(self.vcr_cassette_name)
        self.vcr = _vcr.__enter__()
        self.addCleanup(_vcr.__exit__)

    def gql_client(self, query, qargs):
        """
        Helper utility for sending authenticated graphql requests to flask app over werkzeug client.
        """
        body = {
            'query': query,
            'variables': qargs
        }
        headers = {
            'X-Hasura-Access-Key': 'devaccess',
            'X-Hasura-User-Id': const.HASURA_CLIENT_USER_ID,
            'X-Hasura-Role': 'admin',
        }
        response = self.client.post(
            path='/graphql',
            headers=headers,
            content_type='application/json',
            data=json.dumps(body),
        )
        return response
