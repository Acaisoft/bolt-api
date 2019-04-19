FROM python:3.6.8-alpine3.9 as base
RUN apk --update upgrade

FROM base as builder

RUN mkdir /install
WORKDIR /install

RUN apk add --no-cache openssl-dev
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev
COPY requirements/core.txt /requirements.txt
RUN pip install --no-cache-dir -U pip
RUN pip install --install-option="--prefix=/install" -r /requirements.txt
RUN apk del .build-deps gcc musl-dev libffi-dev

FROM base
COPY --from=builder /install /usr/local

RUN mkdir /app
COPY app /app/app
COPY instance /app/instance
COPY wsgi.py /app/wsgi.py
COPY bolt-deployer/sdk /app/bolt-deployer/sdk
RUN pip install /app/bolt-deployer/sdk
WORKDIR /app

ARG release
ENV SENTRY_RELEASE $release

CMD gunicorn wsgi:application -w 8 --bind 0.0.0.0:80
