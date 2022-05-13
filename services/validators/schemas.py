from marshmallow import Schema
from marshmallow import fields


class ValidateRepositorySchema(Schema):
    repository_url = fields.Str(required=True)
