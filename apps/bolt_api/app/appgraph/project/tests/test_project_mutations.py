from services.testing.testing_util import BoltCase


class TestProjectMutations(BoltCase):
    # TODO: add testing uploads (maybe with mock google storage)

    # recorded created project
    o = {
        'id': BoltCase.recorded_project_id,
        'name': 'test project 1',
        'description': 'test project description',
    }
    u = {
        'id': BoltCase.recorded_project_id,
        'name': 'new name',
        'description': 'new description',
    }

    def test_create_project(self):
        resp = self.gql_client('''mutation ($name:String!, $description:String!) {
            testrun_project_create (
                name:$name
                description:$description
            ) { returning {id name description} }
        }''', {'name': self.o['name'], 'description': self.o['description']})
        self.assertIsNone(resp.errors(), 'expected no errors')
        self.assertCountEqual(self.o, resp.one('testrun_project_create'), 'expected returned data to match')

    def test_update_project(self):
        resp = self.gql_client('''mutation ($id:UUID!, $name:String!, $description:String!) {
            testrun_project_update (
                id: $id
                name: $name
                description: $description
            ) { returning { id name description } }
        }''', self.u)
        self.assertIsNone(resp.errors(), 'expected no errors')
        self.assertCountEqual(self.u, resp.one('testrun_project_update'), 'expected data to have been updated')

    def test_soft_delete_project(self):
        resp = self.gql_client('''mutation ($id:UUID!) {
            testrun_project_delete (
                pk: $id
            ) { returning { id name description } }
        }''', {'id': self.o['id']})
        self.assertIsNone(resp.errors(), 'expected no errors')
        self.assertCountEqual(self.u, resp.one('testrun_project_delete'), 'expected data to have been returned')

    def test_project_summary(self):
        resp = self.gql_client('''query {
            testrun_project_summary { projects { name description } }
        }''', {})
        self.assertIsNone(resp.errors(), 'expected no errors')
        self.assertEqual(6, len(resp.json()['data']['testrun_project_summary']['projects']))
