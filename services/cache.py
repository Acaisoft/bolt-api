from redis import Redis

_cache = None


def get_cache(config, current_app=None):
    global _cache
    if not _cache:
        host = config.get('REDIS_HOST')
        port = config.get('REDIS_PORT')
        passwd = config.get('REDIS_PASS', None)
        dbi = config.get('REDIS_DB')
        if current_app:
            current_app.logger.info(f'connecting redis at {host}:{port}/{dbi} with pass:{bool(passwd)}')
        _cache = Redis(host=host, port=port, password=passwd, db=dbi)
    return _cache
