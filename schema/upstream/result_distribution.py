import typing
from datetime import datetime

from schema.upstream.base import BaseQuery, InputType


class ResultDistribution(typing.NamedTuple, InputType):
    execution_id: str
    start: datetime
    end: datetime
    request_result: dict
    distribution_result: dict


class Query(BaseQuery):
    input_type = ResultDistribution
