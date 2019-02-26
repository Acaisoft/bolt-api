
def validate_time(value: str):
    assert value, 'test duration parameter is required'
    assert value.isdigit(), f'expected numeric value of seconds for duration, got {value}'
    assert int(value) <= 1800, 'maximum testrun duration is 30 minutes or 1800 seconds'


def validate_users(value: str):
    assert value, 'number of users is required'
    assert value.isdigit(), f'expected numeric value for number of users, got {value}'
    assert int(value) <= 5000, 'maximum simultaneous users limit is 5000'


def validate_rampup(value: str):
    assert value, 'user rampup rate is required'
    assert value.isdigit(), f'expected numeric value for user rampup, got {value}'
    assert int(value) <= 1000, 'maximum users ramp up is 1000'


def validate_host(value: str):
    assert value, 'hostname is required'
    assert len(value) > 10, 'hostname too short'
    assert value.startswith('http://') or value.startswith('https://'), f'missing protocol in {value}'


def validate_name(value: str):
    assert value, 'name is required'
    assert len(value) > 2, 'name is too short'


VALIDATORS = {
    '-t': validate_time,
    '-c': validate_users,
    '-r': validate_rampup,
    '-H': validate_host,
}
