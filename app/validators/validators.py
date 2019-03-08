
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


def validate_url(value: str, required=True, key='hostname'):
    if required:
        assert value, f'{key} is required'
    if value:
        assert len(value) > 10, f'{key} too short'
        assert value.startswith('http://') or value.startswith('https://'), f'missing protocol in {key} ({value})'


def validate_text(value: str, required=True, key='name'):
    if required:
        assert value, f'{key} is required'
    if value:
        assert len(value) > 2, f'{key} is too short'
        assert len(value) <= 512, f'{key} is too long'


VALIDATORS = {
    '-t': validate_time,
    '-c': validate_users,
    '-r': validate_rampup,
    '-H': validate_url,
}
