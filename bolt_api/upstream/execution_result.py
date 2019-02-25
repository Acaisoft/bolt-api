import typing
from bolt_api.upstream.base import BaseQuery, InputType


# TODO: WE DONT USING THIS ALREADY. DELETE THIS FROM CODE AND DATABASE
class Result(typing.NamedTuple, InputType):
    execution_id: str
    endpoint: str
    exception: str
    request_type: str
    response_length: str
    response_time: str
    status: str
    timestamp: str


class Query(BaseQuery):
    input_type = Result
