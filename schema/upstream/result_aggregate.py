import string
from collections import namedtuple

from schema.upstream.base import BaseQuery


class ResultAggregate(BaseQuery):
    input_type = namedtuple("result_aggregate", [
        "execution_id",
        "timestamp",
        "fail",
        "av_resp_time",
        "succes",
        "error",
        "av_size",
    ])

    object_template = string.Template('''{
        execution_id:"$execution_id",
        timestamp:$timestamp,
        fail:$fail,
        av_resp_time:"$av_resp_time",
        succes:"$succes",
        error:"$error",
        av_size:"$av_size",
    },''')
