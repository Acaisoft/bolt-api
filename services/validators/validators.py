from services import const


def validate_time(value: str):
    value = value.strip()
    assert value, 'test duration parameter is required'
    assert value.isdigit(), f'expected numeric value of seconds for duration, got {value}'
    assert int(value) <= const.TESTRUN_MAX_DURATION, f'maximum testrun duration {const.TESTRUN_MAX_DURATION} seconds'
    return value


def validate_duration(value: str):
    assert value is not None, 'monitoring duration parameter is required'
    value = value.strip()
    assert value, 'monitoring duration parameter is required'
    assert value.isdigit(), f'expected numeric value of seconds for monitoring duration, got {value}'
    return value


def validate_interval(value: str):
    assert value is not None, 'monitoring interval parameter is required'
    value = value.strip()
    assert value, 'monitoring interval parameter is required'
    assert value.isdigit(), f'expected numeric value of seconds for monitoring interval, got {value}'
    assert int(value) >= const.MONITORING_MIN_INTERVAL, f'monitoring interval must be larger than {const.MONITORING_MIN_INTERVAL}'
    return value


def validate_users(value: str):
    value = value.strip()
    assert value, 'number of users is required'
    assert value.isdigit(), f'expected numeric value for number of users, got {value}'
    assert int(value) <= const.TESTRUN_MAX_USERS, f'maximum simultaneous users limit is {const.TESTRUN_MAX_USERS}'
    return value


def validate_rampup(value: str):
    value = value.strip()
    assert value, 'user rampup rate is required'
    assert value.isdigit(), f'expected numeric value for user rampup, got {value}'
    assert int(value) <= 1000, 'maximum users ramp up is 1000'
    return value


def validate_url(value: str, required=True, key='hostname'):
    value = value.strip()
    if required:
        assert value, f'{key} is required'
    if value:
        assert len(value) > 10, f'{key} too short'
        assert value.startswith('http://') or value.startswith('https://'), f'missing protocol in {key} ({value})'
    return value


def validate_file_path(value: str, required=True, key='file_path'):
    value = value.strip()
    if required:
        assert value, f'{key} is required'
    if value:
        assert len(value) > 4, f'{key} too short'
        assert not value.endswith('.py'), f'don\'t include extension in {key} ({value})'
        assert ('/' not in value) and ('\\' not in value), f'don\'t include path separators in {key} ({value})'
    return value


def validate_repository_branch(value: str, required=True, key='repository_branch'):
    value = value.strip()
    if required:
        assert value, f'{key} is required'
    if value:
        assert len(value) > 4, f'{key} too short'
        assert ' ' not in value, f'spaces not allowed in {key}'
    return value


def validate_text(value: str, required=True, key='name'):
    value = value.strip()
    if required:
        assert value, f'{key} is required'
    if value:
        assert len(value) > 2, f'{key} is too short'
        assert len(value) <= 512, f'{key} is too long'
    return value


def validate_monitoring_chart_configuration(configuration: dict):
    """
    Validates and returns monitoring subset of params.
    >>> validate_monitoring_chart_configuration({ 'charts': [
    ...      {"x_format":"a","node_name":"b","x_data_key":"c","y_format":"d","y_label":"e","title":"f","type":"g","y_data_key":"h"},
    ...      {"x_format":"i","node_name":"j","x_data_key":"k","y_format":"l","y_label":"m","title":"n","type":"o","y_data_key":"p"},
    ... ],},)
    True
    """
    schema = {
        "type": "object",
        "properties": {
            "x_format": {"type": "string"},
            "node_name": {"type": "string"},
            "x_data_key": {"type": "string"},
            "y_format": {"type": "string"},
            "y_label": {"type": "string"},
            "title": {"type": "string"},
            "type": {"type": "string"},
            "y_data_key": {"type": "string"},
        },
    }
    try:
        # TODO fix jsonschema import
        from jsonschema import validate
        from jsonschema import ValidationError

        if configuration.get("charts", None):
            for chart in configuration['charts']:
                try:
                    validate(instance=chart, schema=schema)
                except ValidationError:
                    return False
        else:
            return False

        return True

    except ModuleNotFoundError:
        return True




VALIDATORS = {
    '-t': validate_time,
    '-u': validate_users,
    '-r': validate_rampup,
    '-H': validate_url,
    '-md': validate_duration,
    '-mi': validate_interval,
    '-f': validate_file_path,
    '-b': validate_repository_branch
}

if __name__ == '__main__':
    import doctest

    doctest.testmod()
