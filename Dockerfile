FROM python:3.6-alpine as base

FROM base as builder

RUN apk add --no-cache --virtual .build-deps gcc musl-dev
RUN pip install cython greenlet
RUN apk del .build-deps gcc musl-dev

RUN mkdir /install
WORKDIR /install
COPY requirements/prod.txt /requirements.txt
RUN pip install --install-option="--prefix=/install" -r /requirements.txt

FROM base
COPY --from=builder /install /usr/local

COPY app /app
COPY schema /schema
COPY wsgi.py wsgi.py
WORKDIR /
CMD gunicorn wsgi:application --bind 0.0.0.0:80
