from flask import current_app
from gql import gql

from app.validators.validators import VALIDATORS
from bolt_api.upstream.devclient import devclient


def validate_test_configuration_by_id(test_conf_id):
    conf = devclient(current_app.config).execute(gql('''query ($conf_id:uuid!) {
        configuration (where:{id:{_eq:$conf_id}}) {
            id
            name
            repository {
                url
            }
            configurationParameters {
                value
                parameter {
                    name
                    default_value
                    param_name
                    param_type
                }
            }
        }
    }'''), {'conf_id': str(test_conf_id)})
    assert conf['configuration'], f'configuration not found ({str(conf)})'

    validate_test_configuration(conf['configuration'][0])


def validate_test_configuration(conf: dict):
    """
    check parameter sanity
    >>> validate_test_configuration({
    ...    "name": "conf 1",
    ...    "repository": {
    ...      "url": "http://url.url/url"
    ...    },
    ...    "configurationParameters": [
    ...      {
    ...        "value": "30m",
    ...        "parameter": {
    ...          "name": "time",
    ...          "default_value": "10m",
    ...          "param_name": "-t",
    ...          "param_type": "str"
    ...        }
    ...      },
    ...      {
    ...        "value": "5000",
    ...        "parameter": {
    ...          "name": "users",
    ...          "default_value": "1000",
    ...          "param_name": "-c",
    ...          "param_type": "int"
    ...        }
    ...      },
    ...      {
    ...        "value": "500",
    ...        "parameter": {
    ...          "name": "users/second",
    ...          "default_value": "",
    ...          "param_name": "-r",
    ...          "param_type": "int"
    ...        }
    ...      },
    ...      {
    ...        "value": "http://wp.pl",
    ...        "parameter": {
    ...          "name": "host",
    ...          "default_value": "",
    ...          "param_name": "-H",
    ...          "param_type": "str"
    ...        }
    ...      }
    ... ]})
    Traceback (most recent call last):
    ...
    AssertionError: expected numeric value of seconds for duration, got 30m
    """
    assert len(conf['repository']['url']), 'invalid repository address'

    assert len(conf['name']), 'configuration name is required'

    params = conf['configurationParameters']
    for param in params:
        param_value = param['value']
        param_name = param['parameter']['param_name']
        VALIDATORS[param_name](param_value)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
