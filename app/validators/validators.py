def validate_time(value: str):
    assert value.isdigit(), 'expected numeric value'
    assert int(value) <= 1800, 'maximum testrun duration is 30 minutes or 1800 seconds'


def validate_users(value: str):
    assert value.isdigit(), 'expected numeric value'
    assert int(value) <= 5000, 'maximum simultaneous users limit is 5000'


def validate_rampup(value: str):
    assert value.isdigit(), 'expected numeric value'
    assert int(value) <= 1000, 'maximum users ramp up is 1000'


def validate_host(value: str):
    assert len(value) > 10, 'hostname too short'
    assert value.startswith('http://') or value.startswith('https://'), 'missing protocol'


VALIDATORS = {
    '-t': validate_time,
    '-c': validate_users,
    '-r': validate_rampup,
    '-H': validate_host,
}
