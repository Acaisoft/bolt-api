from services.testing.testing_util import BoltCase


class TestProjectMutations(BoltCase):
    # recorded created project
    o = {
        'id': '04ce4055-5278-4fd5-aab9-2148faa58cdd',
        'name': 'test project 1',
        'description': 'test project description',
    }
    u = {
        'id': o['id'],
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
        self.assertEqual(self.o, resp.one('testrun_project_create'), 'expected returned data to match')

    def test_update_project(self):
        resp = self.gql_client('''mutation ($id:UUID!, $name:String!, $description:String!) {
            testrun_project_update (
                id: $id
                name: $name
                description: $description
            ) { returning { id name description } }
        }''', self.u)
        self.assertIsNone(resp.errors(), 'expected no errors')
        self.assertEqual(self.u, resp.one('testrun_project_update'), 'expected data to have been updated')

    def test_soft_delete_project(self):
        resp = self.gql_client('''mutation ($id:UUID!) {
            testrun_project_delete (
                pk: $id
            ) { returning { id name description } }
        }''', {'id': self.o['id']})
        self.assertIsNone(resp.errors(), 'expected no errors')
        self.assertEqual(self.u, resp.one('testrun_project_delete'), 'expected data to have been returned')

        resp = self.gql_client('''query ($id:UUID!) {
            project_by_pk(id: $id) { id name description is_deleted }
        }''', {'id': self.o['id']})
        exp = self.u.copy()
        exp['is_deleted'] = True
        bod = resp.json()
        print(bod)
        self.assertIsNone(resp.errors(), 'expected no errors')
        self.assertEqual(exp, resp.json()['data']['project_by_pk'], 'expected soft deleted project')
