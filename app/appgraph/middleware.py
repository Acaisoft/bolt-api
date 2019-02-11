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

middleware_list = [timing_middleware]
