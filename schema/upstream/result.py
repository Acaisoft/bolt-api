import string
from collections import namedtuple

from schema.upstream.base import BaseQuery


class Result(BaseQuery):
    input_type = namedtuple("execution_result", [
        "execution_id",
        "endpoint",
        "exception",
        "request_type",
        "response_length",
        "response_time",
        "status",
        "timestamp",
    ])

    object_template = string.Template('''{
      execution_id:"$execution_id",
      endpoint:"$endpoint",
      exception:"$exception",
      request_type:"$request_type",
      response_length:$response_length,
      response_time:$response_time,
      status:"$status",
    },''')
