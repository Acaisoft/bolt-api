from services import const


def request_is_selftest(info):
    """
    Return true if request is mocked, for cases where tests need mocking.
    :param info: wsgi request info
    :return: bool
    """
    return info.context.environ.get(const.SELFTEST_FLAG, None) == const.SELFTEST_FLAG