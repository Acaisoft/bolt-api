FROM python:3.6-alpine as base

FROM base as builder

RUN apk add --no-cache --virtual .build-deps gcc musl-dev openssl-dev libffi-dev
RUN pip install cython greenlet Authlib==0.10
RUN apk del .build-deps gcc musl-dev

RUN mkdir /install
WORKDIR /install
COPY requirements/prod.txt /requirements.txt
RUN pip install --install-option="--prefix=/install" -r /requirements.txt

FROM base
COPY --from=builder /install /usr/local

RUN mkdir /app
COPY app /app/app
COPY instance /app/instance
COPY bolt_api /app/bolt_api
COPY wsgi.py /app/wsgi.py
WORKDIR /app
CMD gunicorn wsgi:application --bind 0.0.0.0:80
