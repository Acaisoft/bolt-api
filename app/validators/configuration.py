from flask import current_app
from gql import gql

from app import const
from app.validators import repository, validate_test_creator
from app.validators.validators import VALIDATORS
from app.hasura_client import hasura_client


def validate_test_configuration_by_id(test_conf_id):
    conf = hasura_client(current_app.config).execute(gql('''query ($conf_id:uuid!) {
        parameter {
            id
            default_value
            param_name
            name
            slug_name
        }
        
        configuration_by_pk (id:$conf_id) {
            id
            name
            
            test_source {
                source_type
                
                project {
                    userProjects { user_id }
                }
                
                repository {
                    name
                    url
                    configuration_type { slug_name }
                    project {
                        userProjects { user_id }
                    }
                }
                
                test_creator {
                    name
                    data
                    min_wait
                    max_wait
                    project {
                        userProjects { user_id }
                    }
                }
            }
            
            configuration_parameters {
                value
                parameter_slug
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
    ...    "configuration_parameters": [
    ...      { "value": "30m", "parameter_slug": "param1", },
    ... ]}, [
    ...      {"slug_name": "param1", "name": "time", "default_value": "360", "param_name": "-t"},
    ... ])
    Traceback (most recent call last):
    ...
    AssertionError: expected numeric value of seconds for duration, got 30m
    """

    assert len(conf['name']), 'configuration name is required'

    validate_test_params(conf['configuration_parameters'], defaults=defaultParams)

    test_source = conf['test_source']
    assert test_source, f'undefined configuration test_source'

    if test_source['source_type'] == const.CONF_SOURCE_REPO:
        assert test_source.get('repository', None), f'repository does not exist'
        repository.validate_accessibility(current_app.config, test_source['repository']['url'])
    elif test_source['source_type'] == const.CONF_SOURCE_JSON:
        assert test_source.get('test_creator', None), f'test_creator does not exist'
        validate_test_creator(
            test_source['test_creator']['data'],
            min_wait=test_source['test_creator']['min_wait'],
            max_wait=test_source['test_creator']['max_wait']
        )


def validate_test_params(params: list, defaults: list) -> dict:
    """
    Validates params and returns input patched with default values from defaults.
    >>> validate_test_params([
    ...      { "value": "30", "parameter_slug": "param1", },
    ...      { "value": "5000", "parameter_slug": "param2", },
    ...      { "value": "500", "parameter_slug": "param3", },
    ...      { "value": "http://wp.pl", "parameter_slug": "param4", },
    ...    ], [
    ...      {"slug_name": "param1", "name": "time", "default_value": "360", "param_name": "-t"},
    ...      {"slug_name": "param2", "name": "users", "default_value": "1000", "param_name": "-c", "param_type": "int"},
    ...      {"slug_name": "param3", "name": "users/second", "default_value": "100", "param_name": "-r", "param_type": "int"},
    ...      {"slug_name": "param4", "name": "host", "default_value": "", "param_name": "-H", "param_type": "str"},
    ... ])
    {'param1': '30', 'param2': '5000', 'param3': '500', 'param4': 'http://wp.pl'}
    """
    params_by_id = dict(((str(x['parameter_slug']), x['value']) for x in params))
    for p in defaults:
        if p['slug_name'] not in params_by_id or not params_by_id[p['slug_name']]:
            params_by_id[p['slug_name']] = p['default_value']

    param_names_by_id = dict(((x['slug_name'], x['param_name']) for x in defaults))
    for parameter_slug, value in params_by_id.items():
        param_name = param_names_by_id.get(parameter_slug, None)
        assert param_name, f'invalid parameter slug "{parameter_slug}"'
        VALIDATORS[param_name](value)

    return params_by_id


if __name__ == '__main__':
    import doctest
    doctest.testmod()
