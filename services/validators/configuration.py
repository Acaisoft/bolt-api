from flask import current_app

from services import const
from services.validators import validate_test_creator
from services.validators.extensions import validate_extensions
from services.validators import repository
from services.validators.validators import VALIDATORS
from services.hasura import hce


def validate_test_configuration_by_id(test_conf_id):
    conf = hce(current_app.config, '''query ($conf_id:uuid!) {
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
            has_load_tests
            has_monitoring
            
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
                
            configuration_extensions {
                type
                extension_params {
                    name
                    value
                }
            }
        }
    }''', {'conf_id': test_conf_id})
    assert conf['configuration_by_pk'], f'configuration not found ({str(conf)})'

    validate_test_configuration(conf['configuration_by_pk'], defaultParams=conf['parameter'])


def validate_test_configuration(conf: dict, defaultParams: list):
    """
    check parameter sanity
    >>> validate_test_configuration({
    ...    "name": "conf 1",
    ...    "test_source": {
    ...        "source_type": "repository",
    ...        "repository": {
    ...          "url": "http://url.url/url"
    ...        },
    ...    },
    ...    "configuration_parameters": [
    ...      { "value": "30m", "parameter_slug": "load_tests_time", },
    ... ]}, [
    ...      {"slug_name": "load_tests_time", "name": "time", "default_value": "360", "param_name": "-t"},
    ... ])
    Traceback (most recent call last):
    ...
    AssertionError: expected numeric value of seconds for duration, got 30m
    """

    assert len(conf['name']), 'configuration name is required'

    if conf['has_load_tests']:
        validate_load_test_params(conf['configuration_parameters'], defaults=defaultParams)

    if conf['has_monitoring']:
        validate_monitoring_params(conf['configuration_parameters'], defaults=defaultParams)

    if not conf['has_monitoring'] and not conf['has_load_tests']:
        raise AssertionError(f'cannot start test without either load_tests or monitoring defined')

    validate_extensions(conf.get('configuration_extensions', []))

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


def validate_load_test_params(params: list, defaults: list) -> dict:
    """
    Validates params and returns input patched with default values from defaults.
    >>> validate_load_test_params([
    ...      { "value": "5000", "parameter_slug": "load_tests_users", },
    ...      { "value": "500", "parameter_slug": "load_tests_rampup", },
    ...      { "value": "http://wp.pl", "parameter_slug": "load_tests_host", },
    ...      { "value": "100", "parameter_slug": "monitoring_duration", },
    ...    ], [
    ...      {"slug_name": "load_tests_time", "name": "time", "default_value": "360", "param_name": "-t"},
    ...      {"slug_name": "load_tests_users", "name": "users", "default_value": "1000", "param_name": "-c", "param_type": "int"},
    ...      {"slug_name": "load_tests_rampup", "name": "users/second", "default_value": "100", "param_name": "-r", "param_type": "int"},
    ...      {"slug_name": "load_tests_host", "name": "host", "default_value": "", "param_name": "-H", "param_type": "str"},
    ...      {"slug_name": "monitoring_duration", "name": "monitoring_duration", "default_value": "", "param_name": "-md", "param_type": "int"},
    ... ])
    {'load_tests_users': '5000', 'load_tests_rampup': '500', 'load_tests_host': 'http://wp.pl', 'load_tests_time': '360'}
    """
    params_by_id = dict(((str(x['parameter_slug']), x['value']) for x in params if x['parameter_slug'].startswith('load_test')))
    load_test_defaults = list(filter(lambda x: x['slug_name'].startswith('load_test'), defaults))
    for p in load_test_defaults:
        if p['slug_name'] not in params_by_id or not params_by_id[p['slug_name']]:
            params_by_id[p['slug_name']] = p['default_value']

    param_names_by_id = dict(((x['slug_name'], x['param_name']) for x in load_test_defaults))
    for parameter_slug, value in params_by_id.items():
        param_name = param_names_by_id.get(parameter_slug, None)
        assert param_name, f'invalid parameter slug "{parameter_slug}"'
        VALIDATORS[param_name](value)

    return params_by_id


def validate_monitoring_params(params: list, defaults: list) -> dict:
    """
    Validates and returns monitoring subset of params.
    >>> validate_monitoring_params([
    ...      { "value": "500", "parameter_slug": "load_tests_rampup", },
    ...      { "value": "100", "parameter_slug": "monitoring_duration", },
    ...    ], [
    ...      {"slug_name": "load_tests_rampup", "name": "users/second", "default_value": "100", "param_name": "-r", "param_type": "int"},
    ...      {"slug_name": "load_tests_host", "name": "host", "default_value": "", "param_name": "-H", "param_type": "str"},
    ...      {"slug_name": "monitoring_duration", "name": "monitoring_duration", "default_value": "", "param_name": "-md", "param_type": "int"},
    ... ])
    {'monitoring_duration': '100'}
    """
    params_by_id = dict(((str(x['parameter_slug']), x['value']) for x in params if x['parameter_slug'].startswith('monitoring_')))
    monitoring_defaults = list(filter(lambda x: x['slug_name'].startswith('monitoring_'), defaults))
    for p in monitoring_defaults:
        if p['slug_name'] not in params_by_id or not params_by_id[p['slug_name']]:
            params_by_id[p['slug_name']] = p['default_value']

    param_names_by_id = dict(((x['slug_name'], x['param_name']) for x in monitoring_defaults))
    for parameter_slug, value in params_by_id.items():
        param_name = param_names_by_id.get(parameter_slug, None)
        assert param_name, f'invalid parameter slug "{parameter_slug}"'
        VALIDATORS[param_name](value)

    return params_by_id


if __name__ == '__main__':
    import doctest

    doctest.testmod()
