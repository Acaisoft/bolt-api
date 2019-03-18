from schematics import types, models


METHOD_CHOICES = (
    'get',
    'post',
    'put',
    'patch',
    'delete'
)

TEST_TYPE_CHOICES = (
    'set',
    'sequence'
)

ASSERT_CHOICES = (
    'response_code',
    'response_time',
    'body_text_equal',
    'body_text_contains'
)


class Assert(models.Model):
    """
    Model for describing custom asserts per endpoint
    Example usage:
        assert_instance = Assert({
            'assert_type': 'body_text_equal',
            'value': 'Hello world',
            'message': 'Text does not exist in body'
        })
    """
    assert_type = types.StringType(choices=ASSERT_CHOICES, required=True)
    value = types.StringType(required=True)
    message = types.StringType(required=True)


class Endpoint(models.Model):
    """
    Model for describing structure of locust endpoints
    Example usage:
        assert_instance = Assert({
            'type': 'response_code',
            'value': '400',
            'message': 'Custom validation error for PUT request'
        })
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
            },
            'headers': {
                'jwt-token': '12345xyz'
            },
            'asserts': [assert_instance]
        })
    """
    name = types.StringType(required=False)
    url = types.StringType(required=True)
    method = types.StringType(choices=METHOD_CHOICES, required=True)
    task_value = types.IntType(default=1)
    payload = types.DictType(types.BaseType, required=False)
    headers = types.DictType(types.StringType, required=False)
    asserts = types.ListType(types.PolyModelType(Assert), required=False)


class TestConfiguration(models.Model):
    """
    Grouped model for describing structure for locust test
    with endpoints, headers, setup/teardown callbacks and variables
    Example usage:
        endpoint = Endpoint({
            'name': 'test',
            'method': 'get',
            'url': '/test',
        })
        test_configuration = TestConfiguration({
            'test_type': 'sequence',
            'endpoints': [endpoint],
            'global_headers': {'k': 'v'},
        })
    """
    test_type = types.StringType(choices=TEST_TYPE_CHOICES, required=True)
    global_headers = types.DictType(types.StringType, required=False)
    setup_endpoints = types.ListType(types.PolyModelType(Endpoint), required=False)
    teardown_endpoints = types.ListType(types.PolyModelType(Endpoint), required=False)
    endpoints = types.ListType(types.PolyModelType(Endpoint), required=True)

    def set_endpoints(self, endpoints):
        if isinstance(endpoints, list):
            list_of_endpoints = []
            for endpoint_data in endpoints:
                list_of_endpoints.append(Endpoint(endpoint_data))
            self.endpoints = list_of_endpoints

    def set_setup_endpoints(self, setup):
        if isinstance(setup, dict) and 'endpoints' in setup.keys() and isinstance(setup['endpoints'], list):
            list_of_endpoints = []
            for endpoint_data in setup['endpoints']:
                list_of_endpoints.append(Endpoint(endpoint_data))
            self.setup_endpoints = list_of_endpoints

    def set_teardown_endpoints(self, teardown):
        if isinstance(teardown, dict) and 'endpoints' in teardown.keys() and isinstance(teardown['endpoints'], list):
            list_of_endpoints = []
            for endpoint_data in teardown['endpoints']:
                list_of_endpoints.append(Endpoint(endpoint_data))
            self.teardown_endpoints = list_of_endpoints
