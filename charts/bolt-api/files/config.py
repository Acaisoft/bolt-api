# config.py

PORT = 80
HASURA_GQL = 'http://hasura.hasura.svc.cluster.local/v1alpha1/graphql'

REDIS_HOST = 'redis-master.redis.svc.cluster.local'
REDIS_PORT = 6379
REDIS_DB = 0

GOOGLE_CLIENT_ID = '397503896505-i6rhbac9sb63uhi05pu3oo6h70tv9vhj.apps.googleusercontent.com'

GITHUB_CLIENT_ID = '6f1b565171e2f15e2afd'

OAUTH_REDIRECT = 'http://localhost:5000'
JWT_ALGORITHM = 'HS256'

CONFIG_VERSION = 1