import typing
from datetime import datetime

from bolt_api.upstream.base import BaseQuery, InputType


class ResultAggregate(typing.NamedTuple, InputType):
    execution_id: str
    timestamp: datetime
    fail: str
    av_resp_time: str
    succes: str
    error: str
    av_size: str


class Query(BaseQuery):
    input_type = ResultAggregate
