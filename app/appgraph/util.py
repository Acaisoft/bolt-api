import graphene
from graphql.language.ast import FragmentSpread


class ValidationInterface(graphene.Interface):
    ok = graphene.Boolean()


class ValidationResponse(graphene.ObjectType):
    class Meta:
        interfaces = (ValidationInterface,)


class ReturnInterface(graphene.Interface):
    affected_rows = graphene.Int()
    returning = graphene.ObjectType()


class ReturnResponse(graphene.ObjectType):
    class Meta:
        interfaces = (ReturnInterface,)


def get_selections(info):
    fragments = info.fragments

    for field_ast in info.field_asts[0].selection_set.selections:
        field_name = field_ast.name.value
        if isinstance(field_ast, FragmentSpread):
            for field in fragments[field_name].selection_set.selections:
                yield field.name.value
            continue

        yield field_name


def get_selected_fields(info):
    return ' '.join([n for n in get_selections(info)])


def get_request_role_userid(info) -> (str, str):
    headers = info.context.headers.environ
    role = headers.get('HTTP_X_HASURA_ROLE', '')
    return role.split(',')[0], headers.get('HTTP_X_HASURA_USER_ID', '').split(',')[0]
