from services.const import MOCK_REPOSITORY
from services.testing.testing_util import BoltCase


class TestRepositoryMutations(BoltCase):

    def test_create_repo(self):
        name = 'test repository 1'
        repo = f'{MOCK_REPOSITORY}/one.git'
        resp = self.gql_client('''mutation ($name:String!, $repo:String!, $id:UUID!) {
            testrun_repository_create (
                name:$name
                project_id:$id
                repository_url:$repo
                type_slug:"load_tests"
            ) { returning { name repository_url type_slug } }
        }''', {
            'id': BoltCase.recorded_project_id,
            'name': name,
            'repo': repo,
        })
        self.assertIsNone(resp.errors(), 'expected no errors')
        self.assertCountEqual({
            'name': name,
            'repository_url': repo,
            'type_slug': 'load_tests',
        }, resp.one('testrun_repository_create'), 'expected repository details')

    def test_update_repo(self):
        name = 'updated repository'
        repo = f'{MOCK_REPOSITORY}/two.git'
        resp = self.gql_client('''mutation ($name:String!, $repo:String!, $id:UUID!) {
            testrun_repository_update (
                id:$id
                name:$name
                repository_url:$repo
            ) { returning { name repository_url } }
        }''', {
            'id': self.recorded_repo_id,
            'name': name,
            'repo': repo,
        })
        self.assertIsNone(resp.errors(), 'expected no errors')
        self.assertCountEqual({
            'name': name,
            'repository_url': repo,
        }, resp.one('testrun_repository_update'), 'expected repository was updated')

    def test_delete_repo(self):
        name = 'updated repository'
        repo = f'{MOCK_REPOSITORY}/two.git'
        resp = self.gql_client('''mutation ($id:UUID!) {
            testrun_repository_delete (
                pk:$id
            ) { returning { name repository_url } }
        }''', {
            'id': self.recorded_repo_id,
        })
        self.assertIsNone(resp.errors(), 'expected no errors')
        self.assertCountEqual({
            'name': name,
            'repository_url': repo,
        }, resp.one('testrun_repository_delete'), 'expected repository data was returned')
