import unittest

from unittest import mock
from schematics import exceptions

from app.models import Assert, Endpoint, TestConfiguration
from app.exceptions import StatusCodeException, TimeException, BodyTextContainsException, BodyTextEqualException


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

    def test_failure_with_response_code(self):
        mocked_response = mock.MagicMock()
        mocked_response.status_code = 200
        assert_instance = Assert({'assert_type': 'response_code', 'value': '400', 'message': 'Wrong response code'})
        validated_data = assert_instance.check_response_for_failure(mocked_response)
        self.assertEqual(validated_data.__class__.__name__, StatusCodeException.__name__)
        self.assertEqual(assert_instance.message, str(validated_data))

    def test_pass_with_response_code(self):
        mocked_response = mock.MagicMock()
        mocked_response.status_code = 404
        assert_instance = Assert({'assert_type': 'response_code', 'value': '404', 'message': 'Wrong response code'})
        self.assertIsNone(assert_instance.check_response_for_failure(mocked_response))

    def test_failure_with_response_time(self):
        mocked_response = mock.MagicMock()
        mocked_response.elapsed.total_seconds.return_value = 2.123456  # mcs
        assert_instance = Assert({'assert_type': 'response_time', 'value': '2122', 'message': 'Wrong response time'})
        validated_data = assert_instance.check_response_for_failure(mocked_response)
        self.assertEqual(validated_data.__class__.__name__, TimeException.__name__)
        self.assertEqual(assert_instance.message, str(validated_data))

    def test_pass_with_response_time(self):
        mocked_response = mock.MagicMock()
        mocked_response.elapsed.total_seconds.return_value = 2.123456  # mcs
        assert_instance = Assert({'assert_type': 'response_time', 'value': '2124', 'message': 'Wrong response code'})
        self.assertIsNone(assert_instance.check_response_for_failure(mocked_response))

    def test_failure_with_body_text_equal(self):
        mocked_response = mock.MagicMock()
        mocked_response.text = 'hi there'
        assert_instance = Assert({'assert_type': 'body_text_equal', 'value': 'hello world', 'message': 'Wrong text'})
        validated_data = assert_instance.check_response_for_failure(mocked_response)
        self.assertEqual(validated_data.__class__.__name__, BodyTextEqualException.__name__)
        self.assertEqual(assert_instance.message, str(validated_data))

    def test_pass_with_body_text_equal(self):
        mocked_response = mock.MagicMock()
        mocked_response.text = 'hello world'
        assert_instance = Assert({'assert_type': 'body_text_equal', 'value': 'hello world', 'message': 'Wrong text'})
        self.assertIsNone(assert_instance.check_response_for_failure(mocked_response))

    def test_failure_with_body_text_contains(self):
        mocked_response = mock.MagicMock()
        mocked_response.text = 'wow. hi man'
        assert_instance = Assert({'assert_type': 'body_text_contains', 'value': 'hello', 'message': 'Wrong text'})
        validated_data = assert_instance.check_response_for_failure(mocked_response)
        self.assertEqual(validated_data.__class__.__name__, BodyTextContainsException.__name__)
        self.assertEqual(assert_instance.message, str(validated_data))

    def test_pass_with_body_text_contains(self):
        mocked_response = mock.MagicMock()
        mocked_response.text = 'Wow. Hi there. My name is locust.'
        assert_instance = Assert({'assert_type': 'body_text_contains', 'value': 'Hi there', 'message': 'Wrong text'})
        self.assertIsNone(assert_instance.check_response_for_failure(mocked_response))


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
            'asserts': None
        })

    def test_model_with_wrong_method_field_data(self):
        endpoint = Endpoint({'name': 'test', 'method': 'unknown', 'url': '/test'})
        with self.assertRaises(exceptions.DataError) as context:
            endpoint.validate()
        self.assertEqual(
            context.exception.to_primitive(),
            {'method': ["Value must be one of ('get', 'post', 'put', 'patch', 'delete')."]}
        )

    def test_model_kwargs(self):
        endpoint = Endpoint({
            'name': 'test', 'method': 'put', 'url': '/test',
            'payload': {'username': 'user', 'password': '1234'},
            'headers': {'auth': 'jwt'}
        })
        self.assertIsNone(endpoint.validate())
        self.assertEqual(endpoint.kwargs, {
            'name': 'test',
            'data': {'username': 'user', 'password': '1234'},
            'headers': {'auth': 'jwt'}
        })

    def test_model_empty_kwargs(self):
        endpoint = Endpoint({'method': 'delete', 'url': '/test', 'task_value': 5})
        self.assertIsNone(endpoint.validate())
        self.assertEqual(endpoint.kwargs, {})

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
            'asserts': None
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
            'asserts': None
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

    def test_asserts_field_with_invalid_types_data(self):
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
                'asserts': None
            }],
            'global_headers': {'global': 'header'},
            'teardown_endpoints': None,
            'setup_endpoints': None
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
            'endpoints': [
                {
                    'name': '#1',
                    'url': '/url1',
                    'method': 'get',
                    'task_value': 1,
                    'payload': None,
                    'headers': None,
                    'asserts': None
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
                    }]
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
                'asserts': None
            }],
            'teardown_endpoints': None,
            'endpoints': [{
                'name': '#1',
                'url': '/url1',
                'method': 'get',
                'task_value': 1,
                'payload': None,
                'headers': None,
                'asserts': None
            }]
        })

    def test_set_teardown_endpoints(self):
        test_configuration = TestConfiguration({'test_type': 'sequence'})
        endpoints = [{'name': '#1', 'url': '/url1', 'method': 'put'}]
        test_configuration.set_endpoints(endpoints)
        teardown_endpoints = {
            'endpoints': [
                {'name': '#2', 'url': '/url2', 'method': 'post', 'payload': {'hello': 'world'}},
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
                'asserts': None
            }],
            'setup_endpoints': None,
            'endpoints': [{
                'name': '#1',
                'url': '/url1',
                'method': 'put',
                'task_value': 1,
                'payload': None,
                'headers': None,
                'asserts': None
            }]
        })

    def test_set_endpoint_headers_with_empty_global_headers(self):
        test_configuration = TestConfiguration({'test_type': 'set'})
        endpoints = [
            {'name': '#1', 'url': '/url1', 'method': 'post', 'headers': {'key1': 'value1', 'key2': 'value2'}}
        ]
        test_configuration.set_endpoints(endpoints)
        self.assertIsNone(test_configuration.validate())
        self.assertEqual(test_configuration.to_primitive(), {
            'test_type': 'set',
            'global_headers': None,
            'teardown_endpoints': None,
            'setup_endpoints': None,
            'endpoints': [{
                'name': '#1',
                'url': '/url1',
                'method': 'post',
                'task_value': 1,
                'payload': None,
                'headers': {
                    'key1': 'value1',
                    'key2': 'value2'
                },
                'asserts': None
            }]
        })

    def test_set_empty_endpoint_headers_with_global_headers(self):
        test_configuration = TestConfiguration({
            'test_type': 'set',
            'global_headers': {
                'global_1': 'value_1',
                'global_2': 'value_2'
            }
        })
        endpoints = [{'name': '#1', 'url': '/url1', 'method': 'post'}]
        test_configuration.set_endpoints(endpoints)
        self.assertIsNone(test_configuration.validate())
        self.assertEqual(test_configuration.to_primitive(), {
            'test_type': 'set',
            'global_headers': {
                'global_1': 'value_1',
                'global_2': 'value_2'
            },
            'teardown_endpoints': None,
            'setup_endpoints': None,
            'endpoints': [{
                'name': '#1',
                'url': '/url1',
                'method': 'post',
                'task_value': 1,
                'payload': None,
                'headers': {
                    'global_1': 'value_1',
                    'global_2': 'value_2'
                },
                'asserts': None
            }]
        })

    def test_set_endpoint_headers_with_global_headers(self):
        test_configuration = TestConfiguration({
            'test_type': 'set',
            'global_headers': {
                'global_1': 'value_1',
                'global_2': 'value_2',
                'common': 'global value'
            }
        })
        endpoints = [{
            'name': '#1',
            'url': '/url1',
            'method': 'post',
            'headers': {
                'common': 'new value',
                'endpoint_1': 'endpoint_1',
                'endpoint_2': 'endpoint_2'
            }
        }]
        test_configuration.set_endpoints(endpoints)
        self.assertIsNone(test_configuration.validate())
        self.assertEqual(test_configuration.to_primitive(), {
            'test_type': 'set',
            'teardown_endpoints': None,
            'setup_endpoints': None,
            'global_headers': {
                'global_1': 'value_1',
                'global_2': 'value_2',
                'common': 'global value'
            },
            'endpoints': [{
                'name': '#1',
                'url': '/url1',
                'method': 'post',
                'task_value': 1,
                'payload': None,
                'headers': {
                    'global_1': 'value_1',
                    'global_2': 'value_2',
                    'common': 'new value',
                    'endpoint_1': 'endpoint_1',
                    'endpoint_2': 'endpoint_2'
                },
                'asserts': None
            }]
        })
