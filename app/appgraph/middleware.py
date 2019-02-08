import logging
from time import time as timer

logger = logging.getLogger(__name__)


def timing_middleware(next, root, info, **args):
    start = timer()
    return_value = next(root, info, **args)
    duration = timer() - start
    logger.debug("{parent_type}.{field_name}: {duration} ms".format(
        parent_type=root._meta.name if root and hasattr(root, '_meta') else '',
        field_name=info.field_name,
        duration=round(duration * 1000, 2)
    ))
    return return_value


def auth_middleware(next, root, info, **args):
    # pull authinfo from flask request
    info.context.authorization = {
        'user': '1',
        'roles': [0, 2],
        'projects': ['p1', 'p2'],
    }
    return next(root, info, **args)


middleware_list = [timing_middleware, auth_middleware]
