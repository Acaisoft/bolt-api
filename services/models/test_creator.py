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

ASSERT_TYPE_CHOICES = (
    'response_code',
    'response_time',
    'body_text_equal',
    'body_text_contains'
)

ACTION_TYPE_CHOICES = (
    'set_variable',
)

ACTION_LOCATION_CHOICES = (
    'response',
    'headers',
    'cookies'
)


class Action(models.Model):
    """
    Model for describing pre/post actions for request (endpoint)
    Example of usage:
        action = Action({
            'action_type': 'set_variable',
            'location': 'response',
            'variable_name': 'token',
            'variable_path': 'auth.token'
        })
    """
    action_type = types.StringType(choices=ACTION_TYPE_CHOICES, required=True)
    location = types.StringType(choices=ACTION_LOCATION_CHOICES, required=True)
    variable_name = types.StringType(required=True)
    variable_path = types.StringType(required=True)


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
    assert_type = types.StringType(choices=ASSERT_TYPE_CHOICES, required=True)
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
        action_instance = Action({
            'action_type': 'set_variable',
            'location': 'response',
            'variable_name': 'token',
            'variable_path': 'auth.token'
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
            'asserts': [assert_instance],
            'actions': [action_instance]
        })
    """
    name = types.StringType(required=False)
    url = types.StringType(required=True)
    method = types.StringType(choices=METHOD_CHOICES, required=True)
    task_value = types.IntType(default=1)
    payload = types.DictType(types.BaseType, required=False)
    headers = types.DictType(types.StringType, required=False)
    asserts = types.ListType(types.PolyModelType(Assert), required=False)
    actions = types.ListType(types.PolyModelType(Action), required=False)


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
    on_start_endpoints = types.ListType(types.PolyModelType(Endpoint), required=False)
    on_stop_endpoints = types.ListType(types.PolyModelType(Endpoint), required=False)
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

    def set_on_start_endpoints(self, on_start):
        if isinstance(on_start, dict) and 'endpoints' in on_start.keys() and isinstance(on_start['endpoints'], list):
            list_of_endpoints = []
            for endpoint_data in on_start['endpoints']:
                list_of_endpoints.append(Endpoint(endpoint_data))
            self.on_start_endpoints = list_of_endpoints

    def set_on_stop_endpoints(self, on_stop):
        if isinstance(on_stop, dict) and 'endpoints' in on_stop.keys() and isinstance(on_stop['endpoints'], list):
            list_of_endpoints = []
            for endpoint_data in on_stop['endpoints']:
                list_of_endpoints.append(Endpoint(endpoint_data))
            self.on_stop_endpoints = list_of_endpoints
