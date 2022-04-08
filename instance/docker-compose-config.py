
KEYCLOAK_URL = 'https://keycloak.dev.bolt.acaisoft.io/auth/'
KEYCLOAK_CLIENT_ID = 'test-runner'
KEYCLOAK_REALM_NAME = 'Bolt'

PORT = 5000

JWT_ALGORITHM = 'HS256'

HASURA_GQL = "http://hasura:8080/v1alpha1/graphql"
HCE_DEBUG = False

# BOLT_DEPLOYER_ADDR = 'localhost:7777'
BOLT_DEPLOYER_ADDR = 'bolt-deployer:80'

SELFSIGNED_TOKEN_FOR_TESTRUNNER = True

REDIS_HOST = 'redis'
REDIS_PORT = 6379
REDIS_DB = 0

BUCKET_PUBLIC_UPLOADS = 'media.bolt.acaisoft.io'
BUCKET_PRIVATE_STORAGE = 'uploads-bolt-acaisoft'
UPLOADS_PUBSUB_SUBSCRIPTION = 'uploads-bolt-acaisoft'
GOOGLE_APPLICATION_CREDENTIALS = 'instance/acai-bolt-356aea83d223.json'

CONFIG_VERSION = '01betaConf'
