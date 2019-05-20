
KEYCLOAK_URL = 'https://keycloak.dev.bolt.acaisoft.io/auth/'
KEYCLOAK_CLIENT_ID = 'test-runner'
KEYCLOAK_REALM_NAME = 'Bolt'

PORT = 5000

OAUTH_REDIRECT = 'http://localhost:5000'

JWT_ALGORITHM = 'HS256'

HASURA_GQL = "http://hasura:8080/v1alpha1/graphql"
# HASURA_GQL = "https://hasura.dev.bolt.acaisoft.io/v1alpha1/graphql"

HCE_DEBUG = True

BOLT_DEPLOYER_ADDR = 'localhost:7777'

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

BUCKET_PUBLIC_UPLOADS = 'media.bolt.acaisoft.io'
UPLOADS_PUBSUB_SUBSCRIPTION = 'gcf-read-bolt-media-request-uploads-bolt-acaisoft'

CONFIG_VERSION = '01beta'
