from redis import Redis

_cache = None


def get_cache(config):
    global _cache
    if not _cache:
        host = config.get('REDIS_HOST', 'localhost')
        port = int(config.get('REDIS_PORT', '6379'))
        rdb = int(config.get('REDIS_DB', '0'))
        _cache = Redis(host=host, port=port, db=rdb)
    return _cache
