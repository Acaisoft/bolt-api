import string
from collections import namedtuple

from schema.upstream.base import BaseQuery


class User(BaseQuery):
    input_type = namedtuple("user", [
        "email",
        "active",
    ])

    object_template = string.Template('''{
      email:"$email",
      active:"$active",
    },''')

