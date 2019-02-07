FROM hasura/graphql-engine:v1.0.0-alpha37.cli-migrations

ARG POSTGRES_SERVER="postgres://postgres:@localhost:5432/postgres"

ADD hasura/migrations /hasura-migrations

ENV HASURA_GRAPHQL_DATABASE_URL $POSTGRES_SERVER
ENV HASURA_GRAPHQL_ENABLE_CONSOLE "true"

CMD ["graphql-engine", "serve"]