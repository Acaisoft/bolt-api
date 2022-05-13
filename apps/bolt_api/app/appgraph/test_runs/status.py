import pathlib

import graphene


class StatusResponseInterface(graphene.Interface):
    status = graphene.String()
    debug = graphene.String()


class StatusResponse(graphene.ObjectType):
    class Meta:
        description = ''
        interfaces = (StatusResponseInterface,)


class TestrunQueries(graphene.ObjectType):
    testrun_repository_key = graphene.String(
        name='testrun_repository_key',
        description='Returns id rsa public key. Use it to give Bolt access to repository containing tests.'
    )

    def resolve_testrun_repository_key(self, info, **kwargs):
        with pathlib.Path.home().joinpath('.ssh', 'id_rsa.pub').open() as fd:
            public_ssh_key = fd.read().strip()
        return public_ssh_key
