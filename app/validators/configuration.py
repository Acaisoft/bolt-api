from flask import current_app
from gql import gql

from app.validators.validators import VALIDATORS
from bolt_api.upstream.devclient import devclient


def validate_test_configuration_by_id(test_conf_id):
    conf = devclient(current_app.config).execute(gql('''query ($conf_id:uuid!) {
        parameter {
            id
            default_value
            param_name
            name
        }
        configuration_by_pk (id:$conf_id) {
            id
            name
            repository {
                url
            }
            configurationParameters {
                value
                parameter_id
            }
        }
    }'''), {'conf_id': test_conf_id})
    assert conf['configuration_by_pk'], f'configuration not found ({str(conf)})'

    validate_test_configuration(conf['configuration_by_pk'], defaultParams=conf['parameter'])


def validate_test_configuration(conf: dict, defaultParams:list):
    """
    check parameter sanity
    >>> validate_test_configuration({
    ...    "name": "conf 1",
    ...    "repository": {
    ...      "url": "http://url.url/url"
    ...    },
    ...    "configurationParameters": [
    ...      { "value": "30m", "parameter_id": "param1", },
    ... ]}, [
    ...      {"id": "param1", "name": "time", "default_value": "360", "param_name": "-t"},
    ... ])
    Traceback (most recent call last):
    ...
    AssertionError: expected numeric value of seconds for duration, got 30m
    """
    assert len(conf['repository']['url']), 'invalid repository address'

    assert len(conf['name']), 'configuration name is required'

    validate_test_params(conf['configurationParameters'], defaults=defaultParams)


def validate_test_params(params: list, defaults: list) -> dict:
    """
    Validates params and returns input patched with default values from defaults.
    >>> validate_test_params([
    ...      { "value": "30", "parameter_id": "param1", },
    ...      { "value": "5000", "parameter_id": "param2", },
    ...      { "value": "500", "parameter_id": "param3", },
    ...      { "value": "http://wp.pl", "parameter_id": "param4", },
    ...    ], [
    ...      {"id": "param1", "name": "time", "default_value": "360", "param_name": "-t"},
    ...      {"id": "param2", "name": "users", "default_value": "1000", "param_name": "-c", "param_type": "int"},
    ...      {"id": "param3", "name": "users/second", "default_value": "100", "param_name": "-r", "param_type": "int"},
    ...      {"id": "param4", "name": "host", "default_value": "", "param_name": "-H", "param_type": "str"},
    ... ])
    {'param1': '30', 'param2': '5000', 'param3': '500', 'param4': 'http://wp.pl'}
    """
    params_by_id = dict(((str(x['parameter_id']), x['value']) for x in params))
    for p in defaults:
        if p['id'] not in params_by_id or not params_by_id[p['id']]:
            params_by_id[p['id']] = p['default_value']

    param_names_by_id = dict(((x['id'], x['param_name']) for x in defaults))
    for parameter_id, value in params_by_id.items():
        param_name = param_names_by_id[parameter_id]
        VALIDATORS[param_name](value)

    return params_by_id


if __name__ == '__main__':
    import doctest
    doctest.testmod()
