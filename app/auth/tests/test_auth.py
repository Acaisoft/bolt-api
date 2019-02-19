from unittest import TestCase

from gql import gql

from upstream.devclient import devclient


class TestAuth(TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.client = devclient({'test': '123'})

    def test_query(self):
        query = '''query ($email: String!) {
            user(where:{email:{_eq:$email}}) { id email active is_admin is_manager is_reader }
        }'''
        resp = self.client.execute(gql(query), variable_values={'email': 'bob@sin.clair'})
        assert resp['data']['user'], 'expected something in response'
