import unittest

from schematics import exceptions

from app.models import Action, Assert, Endpoint, TestConfiguration


class TestActionModel(unittest.TestCase):
    def test_model_without_data(self):
        action = Action()
        with self.assertRaises(exceptions.DataError) as context:
            action.validate()
        self.assertEqual(context.exception.to_primitive(), {
            'action_type': ['This field is required.'],
            'location': ['This field is required.'],
            'variable_name': ['This field is required.'],
            'variable_path': ['This field is required.']
        })

    def test_model_with_wrong_action_type_field(self):
        action = Action({
            'action_type': 'unknown',
            'location': 'response',
            'variable_name': 'token',
            'variable_path': 'auth.token'
        })
        with self.assertRaises(exceptions.DataError) as context:
            action.validate()
        self.assertEqual(context.exception.to_primitive(), {'action_type': ["Value must be one of ('set_variable',)."]})

    def test_model_with_wrong_location_field(self):
        action = Action({
            'action_type': 'set_variable',
            'location': 'unknown',
            'variable_name': 'token',
            'variable_path': 'auth.token'
        })
        with self.assertRaises(exceptions.DataError) as context:
            action.validate()
        self.assertEqual(context.exception.to_primitive(), {
            'location': ["Value must be one of ('response', 'headers', 'cookies')."]})

    def test_model_with_valid_data(self):
        action = Action({
            'action_type': 'set_variable',
            'location': 'headers',
            'variable_name': 'token',
            'variable_path': 'auth.token'
        })
        self.assertIsNone(action.validate())


class TestAssertModel(unittest.TestCase):
    def test_model_without_data(self):
        assert_instance = Assert()
        with self.assertRaises(exceptions.DataError) as context:
            assert_instance.validate()
        self.assertEqual(context.exception.to_primitive(), {
            'assert_type': ['This field is required.'],
            'value': ['This field is required.'],
            'message': ['This field is required.']
        })

    def test_model_with_wrong_assert_type_field_data(self):
        assert_instance = Assert({'assert_type': 'unknown', 'value': '1', 'message': 'Error'})
        with self.assertRaises(exceptions.DataError) as context:
            assert_instance.validate()
        self.assertEqual(context.exception.to_primitive(), {
            'assert_type': [
                "Value must be one of ('response_code', 'response_time', 'body_text_equal', 'body_text_contains')."]
        })

    def test_model_with_valid_data(self):
        assert_instance = Assert({'assert_type': 'response_code', 'value': '400', 'message': 'Error 400'})
        self.assertIsNone(assert_instance.validate())


class TestEndpointModel(unittest.TestCase):
    def test_model_without_data(self):
        endpoint = Endpoint()
        with self.assertRaises(exceptions.DataError) as context:
            endpoint.validate()
        self.assertEqual(context.exception.to_primitive(), {
            'url': ['This field is required.'],
            'method': ['This field is required.']
        })

    def test_partial_validation(self):
        endpoint = Endpoint({'method': 'get'})
        with self.assertRaises(exceptions.DataError) as context:
            endpoint.validate()
        self.assertEqual(context.exception.to_primitive(), {'url': ['This field is required.']})

    def test_model_with_valid_data(self):
        endpoint = Endpoint({'method': 'get', 'url': '/test'})
        self.assertIsNone(endpoint.validate())
        self.assertEqual(endpoint.to_primitive(), {
            'name': None,
            'method': 'get',
            'url': '/test',
            'task_value': 1,
            'headers': None,
            'payload': None,
            'asserts': None,
            'actions': None
        })

    def test_model_with_wrong_method_field_data(self):
        endpoint = Endpoint({'name': 'test', 'method': 'unknown', 'url': '/test'})
        with self.assertRaises(exceptions.DataError) as context:
            endpoint.validate()
        self.assertEqual(
            context.exception.to_primitive(),
            {'method': ["Value must be one of ('get', 'post', 'put', 'patch', 'delete')."]}
        )

    def test_payload_field_with_valid_combined_data(self):
        endpoint = Endpoint({
            'name': 'test',
            'method': 'put',
            'url': '/test',
            'task_value': 2,
            'payload': {
                'roles': ['admin', 'user'],
                'ids': [1, 2, 99],
                'kebab': 'cebula',
                'simple_dict': {'key': 'value'},
                'combined_dict': {'test': [1, 2, '3'], 'task': 1}
            }
        })
        self.assertIsNone(endpoint.validate())
        self.assertEqual(endpoint.to_primitive(), {
            'name': 'test',
            'method': 'put',
            'url': '/test',
            'task_value': 2,
            'payload': {
                'roles': ['admin', 'user'],
                'ids': [1, 2, 99],
                'kebab': 'cebula',
                'simple_dict': {'key': 'value'},
                'combined_dict': {'test': [1, 2, '3'], 'task': 1}
            },
            'headers': None,
            'asserts': None,
            'actions': None
        })

    def test_payload_field_with_empty_dict_data(self):
        endpoint = Endpoint({
            'name': 'test',
            'method': 'put',
            'url': '/test',
            'task_value': 2,
            'payload': {}
        })
        self.assertIsNone(endpoint.validate())
        self.assertEqual(endpoint.to_primitive(), {
            'name': 'test',
            'method': 'put',
            'url': '/test',
            'task_value': 2,
            'payload': {},
            'headers': None,
            'asserts': None,
            'actions': None
        })

    def test_payload_field_with_invalid_types_data(self):
        # as list
        with self.assertRaises(exceptions.DataError) as context:
            Endpoint({'name': 'test', 'method': 'put', 'url': '/test', 'payload': ['1', 2]})
        self.assertEqual(context.exception.to_primitive(), {'payload': ["Only mappings may be used in a DictType"]})
        # as string
        with self.assertRaises(exceptions.DataError) as context:
            Endpoint({'name': 'test', 'method': 'put', 'url': '/test', 'payload': 'String value'})
        self.assertEqual(context.exception.to_primitive(), {'payload': ["Only mappings may be used in a DictType"]})
        # as integer
        with self.assertRaises(exceptions.DataError) as context:
            Endpoint({'name': 'test', 'method': 'put', 'url': '/test', 'payload': 123})
        self.assertEqual(context.exception.to_primitive(), {'payload': ["Only mappings may be used in a DictType"]})
        # as boolean
        with self.assertRaises(exceptions.DataError) as context:
            Endpoint({'name': 'test', 'method': 'put', 'url': '/test', 'payload': True})
        self.assertEqual(context.exception.to_primitive(), {'payload': ["Only mappings may be used in a DictType"]})

    def test_asserts_field_with_invalid_data(self):
        endpoint = Endpoint({
            'name': 'test',
            'method': 'put',
            'url': '/test',
            'task_value': 2,
            'payload': {},
            'asserts': [{
                'assert_type': 'unknown type',
                'value': '100',
                'message': 'Error'
            }]
        })
        with self.assertRaises(exceptions.DataError) as context:
            endpoint.validate()
        self.assertEqual(context.exception.to_primitive(), {
            'asserts': {0: {'assert_type': ["Value must be one of ('response_code', "
                                            "'response_time', 'body_text_equal', 'body_text_contains')."]}}
        })

    def test_assert_field_with_valid_data(self):
        endpoint = Endpoint({
            'name': 'test',
            'method': 'put',
            'url': '/test',
            'task_value': 2,
            'asserts': [
                {
                    'assert_type': 'response_time',
                    'value': '100',
                    'message': 'Error 1'
                },
                {
                    'assert_type': 'body_text_contains',
                    'value': ' hello world',
                    'message': 'Error 2'
                }
            ]
        })
        self.assertIsNone(endpoint.validate())
        self.assertEqual(endpoint.to_primitive(), {
            'name': 'test',
            'method': 'put',
            'url': '/test',
            'task_value': 2,
            'asserts': [
                {
                    'assert_type': 'response_time',
                    'value': '100',
                    'message': 'Error 1'
                },
                {
                    'assert_type': 'body_text_contains',
                    'value': ' hello world',
                    'message': 'Error 2'
                }
            ],
            'payload': None,
            'headers': None,
            'actions': None
        })

    def test_action_field_with_invalid_data(self):
        endpoint = Endpoint({
            'name': 'test',
            'method': 'put',
            'url': '/test',
            'task_value': 2,
            'payload': {},
            'asserts': [{
                'assert_type': 'response_code',
                'value': '100',
                'message': 'Error'
            }],
            'actions': [{
                'action_type': 'unknown',
                'location': 'response',
                'variable_name': 'token',
                'variable_path': 'my_token.path'
            }]
        })
        with self.assertRaises(exceptions.DataError) as context:
            endpoint.validate()
        self.assertEqual(context.exception.to_primitive(), {
            'actions': {0: {'action_type': ["Value must be one of ('set_variable',)."]}}
        })

    def test_action_field_with_valid_data(self):
        endpoint = Endpoint({
            'name': 'test',
            'method': 'put',
            'url': '/test',
            'task_value': 2,
            'payload': {},
            'actions': [
                {
                    'action_type': 'set_variable',
                    'location': 'response',
                    'variable_name': 'token',
                    'variable_path': 'my_token.path'
                },
                {
                    'action_type': 'set_variable',
                    'location': 'cookies',
                    'variable_name': 'token_type',
                    'variable_path': 'token.auth.type'
                }
            ]
        })
        self.assertIsNone(endpoint.validate())
        self.assertEqual(endpoint.to_primitive(), {
            'name': 'test',
            'method': 'put',
            'url': '/test',
            'task_value': 2,
            'payload': {},
            'asserts': None,
            'headers': None,
            'actions': [
                {
                    'action_type': 'set_variable',
                    'location': 'response',
                    'variable_name': 'token',
                    'variable_path': 'my_token.path'
                },
                {
                    'action_type': 'set_variable',
                    'location': 'cookies',
                    'variable_name': 'token_type',
                    'variable_path': 'token.auth.type'
                }
            ]
        })


class TestConfigurationModel(unittest.TestCase):
    def test_model_without_data(self):
        test_configuration = TestConfiguration()
        with self.assertRaises(exceptions.DataError) as context:
            test_configuration.validate()
        self.assertEqual(context.exception.to_primitive(), {
            'test_type': ['This field is required.'],
            'endpoints': ['This field is required.']
        })

    def test_partial_validation(self):
        test_configuration = TestConfiguration({'test_type': 'sequence'})
        with self.assertRaises(exceptions.DataError) as context:
            test_configuration.validate()
        self.assertEqual(context.exception.to_primitive(), {'endpoints': ['This field is required.']})

    def test_model_with_valid_data(self):
        endpoint = Endpoint({'name': 'test', 'method': 'get', 'url': '/test'})
        test_configuration = TestConfiguration({
            'test_type': 'sequence',
            'endpoints': [endpoint],
            'global_headers': {
                'global': 'header'
            }
        })
        self.assertIsNone(test_configuration.validate())
        self.assertEqual(test_configuration.to_primitive(), {
            'test_type': 'sequence',
            'endpoints': [{
                'name': 'test',
                'method': 'get',
                'url': '/test',
                'task_value': 1,
                'payload': None,
                'headers': None,
                'asserts': None,
                'actions': None
            }],
            'global_headers': {'global': 'header'},
            'teardown_endpoints': None,
            'setup_endpoints': None,
            'on_start_endpoints': None,
            'on_stop_endpoints': None
        })

    def test_model_with_wrong_test_type_field_data(self):
        endpoint = Endpoint({'name': 'test', 'method': 'get', 'url': '/test'})
        test_configuration = TestConfiguration({
            'test_type': 'unknown-test-type',
            'endpoints': [
                endpoint
            ],
            'global_headers': {
                'k': 'v'
            }
        })
        with self.assertRaises(exceptions.DataError) as context:
            test_configuration.validate()
        self.assertEqual(context.exception.to_primitive(), {'test_type': ["Value must be one of ('set', 'sequence')."]})

    def test_set_endpoints(self):
        endpoints = [
            {
                'name': '#1',
                'url': '/url1',
                'method': 'get'
            },
            {
                'name': '#2',
                'url': '/url2',
                'method': 'post',
                'payload': {
                    'user': 'user',
                    'pass': 'pass'
                },
                'asserts': [{
                    'assert_type': 'body_text_equal',
                    'value': 'hello world',
                    'message': 'Yes. error !!!'
                }]
            },
            {
                'name': '#3',
                'url': '/url3',
                'method': 'delete',
                'headers': {
                    'jwt-token': '12345xyz'
                },
                'asserts': [
                    {
                        'assert_type': 'response_time',
                        'value': '1000',
                        'message': 'Too slowly'
                    },
                    {
                        'assert_type': 'response_code',
                        'value': '400',
                        'message': 'Error 400'
                    }
                ],
                'actions': [
                    {
                        'action_type': 'set_variable',
                        'location': 'response',
                        'variable_name': 'token',
                        'variable_path': 'auth.token'
                    },
                    {
                        'action_type': 'set_variable',
                        'location': 'cookies',
                        'variable_name': 'date',
                        'variable_path': 'CurrentDate'
                    }
                ]
            }
        ]
        test_configuration = TestConfiguration({'test_type': 'set'})
        test_configuration.set_endpoints(endpoints)
        self.assertIsNone(test_configuration.validate())
        self.assertEqual(test_configuration.to_primitive(), {
            'test_type': 'set',
            'global_headers': None,
            'setup_endpoints': None,
            'teardown_endpoints': None,
            'on_start_endpoints': None,
            'on_stop_endpoints': None,
            'endpoints': [
                {
                    'name': '#1',
                    'url': '/url1',
                    'method': 'get',
                    'task_value': 1,
                    'payload': None,
                    'headers': None,
                    'asserts': None,
                    'actions': None
                },
                {
                    'name': '#2',
                    'url': '/url2',
                    'method': 'post',
                    'task_value': 1,
                    'payload': {
                        'user': 'user',
                        'pass': 'pass'
                    },
                    'headers': None,
                    'asserts': [{
                        'assert_type': 'body_text_equal',
                        'value': 'hello world',
                        'message': 'Yes. error !!!'
                    }],
                    'actions': None
                },
                {
                    'name': '#3',
                    'url': '/url3',
                    'method': 'delete',
                    'task_value': 1,
                    'payload': None,
                    'headers': {
                        'jwt-token': '12345xyz'
                    },
                    'asserts': [
                        {
                            'assert_type': 'response_time',
                            'value': '1000',
                            'message': 'Too slowly'
                        },
                        {
                            'assert_type': 'response_code',
                            'value': '400',
                            'message': 'Error 400'
                        }
                    ],
                    'actions': [
                        {
                            'action_type': 'set_variable',
                            'location': 'response',
                            'variable_name': 'token',
                            'variable_path': 'auth.token'
                        },
                        {
                            'action_type': 'set_variable',
                            'location': 'cookies',
                            'variable_name': 'date',
                            'variable_path': 'CurrentDate'
                        }
                    ]
                }
            ]
        })

    def test_set_setup_endpoints(self):
        test_configuration = TestConfiguration({'test_type': 'set'})
        endpoints = [{'name': '#1', 'url': '/url1', 'method': 'get'}]
        test_configuration.set_endpoints(endpoints)
        setup_endpoints = {
            'endpoints': [
                {'name': '#2', 'url': '/url2', 'method': 'delete'},
            ]
        }
        test_configuration.set_setup_endpoints(setup_endpoints)
        self.assertIsNone(test_configuration.validate())
        self.assertEqual(test_configuration.to_primitive(), {
            'test_type': 'set',
            'global_headers': None,
            'setup_endpoints': [{
                'name': '#2',
                'url': '/url2',
                'method': 'delete',
                'task_value': 1,
                'payload': None,
                'headers': None,
                'asserts': None,
                'actions': None
            }],
            'teardown_endpoints': None,
            'endpoints': [{
                'name': '#1',
                'url': '/url1',
                'method': 'get',
                'task_value': 1,
                'payload': None,
                'headers': None,
                'asserts': None,
                'actions': None
            }],
            'on_start_endpoints': None,
            'on_stop_endpoints': None
        })

    def test_set_teardown_endpoints(self):
        test_configuration = TestConfiguration({'test_type': 'sequence'})
        endpoints = [{'name': '#1', 'url': '/url1', 'method': 'put'}]
        test_configuration.set_endpoints(endpoints)
        teardown_endpoints = {
            'endpoints': [
                {
                    'name': '#2',
                    'url': '/url2',
                    'method': 'post',
                    'payload': {
                        'hello': 'world'
                    },
                    'actions': [{
                        'action_type': 'set_variable',
                        'location': 'headers',
                        'variable_name': 'token',
                        'variable_path': 'auth.token'
                    }]
                },
            ]
        }
        test_configuration.set_teardown_endpoints(teardown_endpoints)
        self.assertIsNone(test_configuration.validate())
        self.assertEqual(test_configuration.to_primitive(), {
            'test_type': 'sequence',
            'global_headers': None,
            'teardown_endpoints': [{
                'name': '#2',
                'url': '/url2',
                'method': 'post',
                'task_value': 1,
                'payload': {
                    'hello': 'world'
                },
                'headers': None,
                'asserts': None,
                'actions': [{
                    'action_type': 'set_variable',
                    'location': 'headers',
                    'variable_name': 'token',
                    'variable_path': 'auth.token'
                }]
            }],
            'setup_endpoints': None,
            'endpoints': [{
                'name': '#1',
                'url': '/url1',
                'method': 'put',
                'task_value': 1,
                'payload': None,
                'headers': None,
                'asserts': None,
                'actions': None
            }],
            'on_start_endpoints': None,
            'on_stop_endpoints': None
        })
