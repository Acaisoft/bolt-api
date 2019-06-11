FROM python:3.6.8-alpine3.9 as base
RUN apk --update upgrade
RUN apk add --no-cache libstdc++ libjpeg zlib
RUN pip install --no-cache-dir -U pip
# ~20 MB

FROM base as builder

RUN mkdir /install
WORKDIR /install

RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev jpeg-dev zlib-dev openssl-dev build-base curl

RUN curl -L https://github.com/argoproj/argo/releases/download/v2.3.0/argo-linux-amd64 > /usr/bin/argo \
  && chmod +x /usr/bin/argo

# ~205 MB
# core requirements for hasura and graphql
COPY apps/bolt_api/requirements/core.txt /requirements_core.txt
RUN pip install --install-option="--prefix=/install" -r /requirements_core.txt
# remove if deploying upload processor separately
COPY apps/bolt_api/requirements/upload_processing.txt /requirements_upload_processing.txt
RUN pip install --install-option="--prefix=/install" -r /requirements_upload_processing.txt
RUN apk del .build-deps

FROM base
COPY --from=builder /install /usr/local
COPY --from=builder /usr/bin/argo /usr/bin/argo

COPY apps /apps
COPY services /services
COPY instance /instance
COPY bolt-deployer/sdk /bolt-deployer/sdk
RUN mkdir /apps/executions
RUN pip install /bolt-deployer/sdk
RUN rm -rf /bolt-deployer/sdk
WORKDIR /

ARG release
ENV SENTRY_RELEASE $release
ENV FLASK_APP=apps.bolt_api.wsgi:application

CMD gunicorn apps.bolt_api.wsgi:application -w 6 --timeout 480 --bind 0.0.0.0:80 --worker-tmp-dir /dev/shm
