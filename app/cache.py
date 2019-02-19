import logging

from redis import Redis

_cache = None


def get_cache(config):
    global _cache
    if not _cache:
        logging.info("connecting redis at %s", config.get('REDIS_HOST'))
        _cache = Redis(
            host=config.get('REDIS_HOST'),
            port=config.get('REDIS_PORT'),
            password=config.get('REDIS_PASS', None),
            db=config.get('REDIS_DB')
        )
    return _cache
