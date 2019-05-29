FROM python:3.6.8-alpine3.9 as base
RUN apk --update upgrade

FROM base as metrics_builder

RUN mkdir /install
WORKDIR /install

RUN apk add --no-cache openssl-dev
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev
COPY apps/bolt_metrics_api/requirements/core.txt /requirements.txt
RUN pip install --no-cache-dir -U pip
RUN pip install --install-option="--prefix=/install" -r /requirements.txt
RUN apk del .build-deps gcc musl-dev libffi-dev

FROM base
COPY --from=metrics_builder /install /usr/local

COPY apps /apps
COPY services /services
COPY instance /instance
WORKDIR /

ARG release
ENV SENTRY_RELEASE $release
ENV FLASK_APP=apps.bolt_metrics_api.wsgi:application

CMD gunicorn apps.bolt_metrics_api.wsgi:application -w 8 --bind 0.0.0.0:80 --worker-tmp-dir /dev/shm
