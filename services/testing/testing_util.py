import json
import logging
import os
import sys
import unittest

import requests
import vcr
from werkzeug.test import Client
from werkzeug.wrappers import Response

from apps.bolt_api.app import create_app
from apps.bolt_api.wsgi import application
from services import const

logging.basicConfig()
vcr_log = logging.getLogger("vcr")
vcr_log.setLevel(logging.INFO)


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
        """helper returning contents from 'repsonse.data.<query_name>.returning' """
        return self.json()['data'][query_name]['returning']


class BoltCase(unittest.TestCase):
    """
    Testcase with vcr and custom graphql client.
    To record responses Hasura must be up and running in development mode.
    """

    recorded_project_id = '04ce4055-5278-4fd5-aab9-2148faa58cdd'
    recorded_repo_id = '04ce4055-5278-4fd5-aab9-2148faa58cdd'
    recorded_config_id = '7262d765-4d18-48a9-9d08-dd142ce8dab5'
    recorded_execution_id = '7262d765-4d18-48a9-9d08-dd142ce8dab5'
    user_role = const.ROLE_ADMIN

    def setUp(self) -> None:
        super().setUp()
        # setup flask client
        application.config.from_mapping(BOLT_API_SELFTEST_FLAG=const.SELFTEST_FLAG)
        self.client = Client(application=application, response_wrapper=BoltResponse)
        # setup vcr context manager
        self.vcr_cassette_name = f'{self.__class__.__name__}.{self._testMethodName}.yaml'
        _vcr = vcr.VCR(
            serializer='json',
            cassette_library_dir=self.cassette_path(),
            record_mode='once',
            match_on=['uri', 'method', 'raw_body'],
            filter_headers=['authorization'],
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
            'X-Hasura-Access-Key': const.HASURA_DEVELOPMENT_ACCESS_KEY,
            'X-Hasura-User-Id': const.HASURA_CLIENT_USER_ID,
            'X-Hasura-Role': self.user_role,
        }
        response = self.client.post(
            path='/graphql',
            headers=headers,
            content_type='application/json',
            data=json.dumps(body),
            environ_overrides={const.SELFTEST_FLAG: const.SELFTEST_FLAG},
        )
        print(response)
        print(response.json())
        return response

    def cassette_path(self):
        parent_here = os.path.dirname(os.path.abspath(sys.modules[self.__class__.__module__].__file__))
        return os.path.join(parent_here, 'fixtures')
