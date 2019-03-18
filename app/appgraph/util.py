from typing import Type

import graphene
from graphql.language.ast import FragmentSpread


def OutputTypeFactory(cls:Type[graphene.ObjectType], postfix=""):
    return type(cls.__name__ + postfix + 'ReturnType', (graphene.ObjectType,), {
        'affected_rows': graphene.Int(),
        'returning': graphene.List(cls),
    })


def OutputInterfaceFactory(cls:Type[graphene.Interface], postfix=""):
    metaclass = type(cls.__name__ + postfix + 'Metaclass', (object,), {'interfaces': (cls, )})
    return_type = type(cls.__name__ + postfix + 'WrappedReturnType', (graphene.ObjectType,), {
        'Meta': metaclass,
    })
    return type(cls.__name__ + postfix + 'WrappingReturnType', (graphene.ObjectType,), {
        'affected_rows': graphene.Int(),
        'returning': graphene.List(return_type),
    })


def OutputValueFromFactory(cls, returning_response):
    output = [cls.Output.returning._of_type(**item) for item in returning_response['returning']]
    return cls.Output(
        affected_rows=len(output),
        returning=output
    )


class ValidationInterface(graphene.Interface):
    ok = graphene.Boolean()


class ValidationResponse(graphene.ObjectType):
    class Meta:
        interfaces = (ValidationInterface,)


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
