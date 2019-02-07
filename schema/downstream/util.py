import typing
from graphql.language.ast import FragmentSpread
from schema import upstream
from schema.upstream.devclient import devclient


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


class ClientsType(typing.NamedTuple):
    user: typing.Any
    repo: typing.Any
    conf: typing.Any


_clients: ClientsType = None


def clients():
    global _clients
    if not _clients:
        cl = devclient()
        _clients = ClientsType(
            user=upstream.user.Query(cl),
            repo=upstream.repository.Query(cl),
            conf=upstream.configuration.Query(cl),
        )
    return _clients
