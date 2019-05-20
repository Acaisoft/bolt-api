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


def validate_text(value: str, required=True, key='name'):
    value = value.strip()
    if required:
        assert value, f'{key} is required'
    if value:
        assert len(value) > 2, f'{key} is too short'
        assert len(value) <= 512, f'{key} is too long'
    return value


VALIDATORS = {
    '-t': validate_time,
    '-c': validate_users,
    '-r': validate_rampup,
    '-H': validate_url,
    '-md': validate_duration,
}
