import typing
from schema.upstream.base import BaseQuery, InputType


class User(typing.NamedTuple, InputType):
    email: str
    active: bool


class Query(BaseQuery):
    input_type = User

