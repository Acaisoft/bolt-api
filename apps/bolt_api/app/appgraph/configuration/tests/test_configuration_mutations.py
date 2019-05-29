import json

from services.projects.demo_project import SMOKE_TEST_TARGET
from services.testing.testing_util import BoltCase


class TestConfigurationMutations(BoltCase):

    def test_create_conf(self):
        name = 'test config 12345'
        resp = self.gql_client('''mutation ($name:String!, $id:UUID!, $testsource_repo_id:UUID!, $test_target:String!) {
            testrun_configuration_create(
                name:$name
                has_load_tests:true
                has_monitoring:true
                project_id:$id
                type_slug:"load_tests"
                test_source_id:$testsource_repo_id
                configuration_envvars:[{
                    name:"testvar"
                    value:"testvarvalue"
                }]
                configuration_parameters:[{
                    parameter_slug:"load_tests_host"
                    value:$test_target
                }, {
                    parameter_slug:"load_tests_duration"
                    value:"30"
                }, {
                    parameter_slug:"monitoring_duration"
                    value:"5"
                }]
            ) { returning { 
                name 
                project_id
                configuration_parameters { value parameter_slug }
                configuration_envvars { name value }
            }}
        }''', {
            'id': self.recorded_project_id,
            'name': name,
            'testsource_repo_id': self.recorded_repo_id,
            'test_target': SMOKE_TEST_TARGET,
        })
        self.assertIsNone(resp.errors(), 'expected no errors')
        out = resp.one('testrun_configuration_create')
        self.assertEqual(name, out['name'], 'expected config to have been created')
        # envvar was saved correctly
        self.assertCountEqual([{
            "name": "testvar",
            "value": "testvarvalue"
        }], out['configuration_envvars'], 'expected environment var does not match')
        # parameters saved and populated with defaults
        self.assertCountEqual([
            {"value": SMOKE_TEST_TARGET, "parameter_slug": "load_tests_host"},
            {"value": "30", "parameter_slug": "load_tests_duration"},
            {"value": "500", "parameter_slug": "load_tests_rampup"},
            {"value": "1000", "parameter_slug": "load_tests_users"},
            {"value": "5", "parameter_slug": "monitoring_duration"},
            {"value": "5", "parameter_slug": "monitoring_interval"}
        ], out['configuration_parameters'], 'expected configuration parameters do not match')

    def test_update_conf(self):
        name = 'updated test config name 12345'
        resp = self.gql_client('''mutation ($name:String!, $id:UUID!, $test_target:String!) {
            testrun_configuration_update(
                id:$id
                name:$name
                has_load_tests:true
                has_monitoring:false
                configuration_envvars:[{
                    name:"testvar_2"
                    value:"testvarvalue 2"
                }]
                configuration_parameters:[{
                    parameter_slug:"load_tests_host"
                    value:$test_target
                }]
            ) { returning { 
                name 
                has_monitoring
                configuration_parameters { value parameter_slug }
                configuration_envvars { name value }
            }}
        }''', {
            'id': self.recorded_config_id,
            'name': name,
            'test_target': SMOKE_TEST_TARGET,
        })
        self.assertIsNone(resp.errors(), 'expected no errors')
        out = resp.one('testrun_configuration_update')
        self.assertEqual(name, out['name'], 'expected config to have been renamed')
        self.assertEqual(False, out['has_monitoring'], 'expected monitoring to have been disabled')
        # envvar was saved correctly
        self.assertCountEqual([{
            "name": "testvar_2",
            "value": "testvarvalue 2"
        }], out['configuration_envvars'], 'expected environment vars to have been updated')
        # parameters saved and populated with defaults
        self.assertCountEqual([
            {"value": SMOKE_TEST_TARGET, "parameter_slug": "load_tests_host"},
            {"value": "10", "parameter_slug": "load_tests_duration"},
            {"value": "500", "parameter_slug": "load_tests_rampup"},
            {"value": "1000", "parameter_slug": "load_tests_users"},
        ], out['configuration_parameters'], 'expected configuration parameters do not match')
        print(json.dumps(out, indent=4))

    def test_delete_conf(self):
        resp = self.gql_client('''mutation ($id:UUID!) {
            testrun_configuration_delete(
                pk:$id
            ) { returning { id } }
        }''', {
            'id': self.recorded_config_id,
        })
        self.assertIsNone(resp.errors(), 'expected no errors')
        self.assertEqual(self.recorded_config_id, resp.one('testrun_configuration_delete')['id'], 'expected config to have been renamed')