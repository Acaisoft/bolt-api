from datetime import datetime


def l2u(locust_timestamp:str) -> float:
    """
    Convert locust timestamp format to unix milisecond
    :param locust_timestamp: input timestamp in format: 2019-04-17T06:53:50.475089+00:00
    :return: float representing input in unix milisecond format
    """
    return datetime.strptime(
        locust_timestamp.replace('+00:00', '+0000'),
        '%Y-%m-%dT%H:%M:%S.%f%z'
    ).timestamp() * 1000


def fields_to_columns(fields_list):
    """
    Return a list of data field names parseable by grafana
    :param fields_list: ['field_a', 'field_b']
    :return: [{"text":"Field A","type":"number"},{"text":"Field B","type":"number"},]
    """
    def m(x:str):
        return x.replace('_', ' ').title()
    return [{'text': 'Time', 'type': 'time'}] + [{'text': m(f), 'type': 'number'} for f in fields_list]
