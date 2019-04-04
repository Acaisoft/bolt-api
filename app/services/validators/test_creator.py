import json

from app.logger import setup_custom_logger
from app.models import TestConfiguration

logger = setup_custom_logger(__name__)


def validate_test_creator(json_data, min_wait, max_wait):
    assert bool(json_data), f'json data is required'
    logger.info(f'Executed validator for Test Creator with data: {json_data}, {min_wait}, {max_wait}')
    try:
        data = json.loads(json_data)
    except json.decoder.JSONDecodeError:
        assert None, 'Error during converting JSON data to python Dict'
    else:
        # validate min/max wait values
        if not isinstance(min_wait, int) or not isinstance(max_wait, int):
            assert None, 'Min wait and Max wait must be integers'
        if min_wait < 50:
            assert None, 'Min wait value should be greater than or equal 50 ms'
        elif max_wait < 100:
            assert None, 'Max wait value should be greater than or equal 100 ms'
        elif min_wait > max_wait:
            assert None, 'Max wait should be greater than Min wait'
        # validate test creator fields
        test_configuration = TestConfiguration({
            'test_type': data.get('test_type'), 'global_headers': data.get('global_headers')})
        test_configuration.set_endpoints(data.get('endpoints'))
        test_configuration.set_setup_endpoints(data.get('setup'))
        test_configuration.set_teardown_endpoints(data.get('teardown'))
        test_configuration.set_on_start_endpoints(data.get('on_start'))
        test_configuration.set_on_stop_endpoints(data.get('on_stop'))
        test_configuration.validate()
