import typing
from datetime import datetime

from bolt_api.upstream.base import BaseQuery, InputType


class Exec(typing.NamedTuple, InputType):
    configuration_id: str
    status: str
    test_preparation_job_id: str
    id: str = None
    start: datetime = None
    end: datetime = None


class Query(BaseQuery):
    input_type = Exec
