import graphene

from app.appgraph.util import get_selected_fields, clients


class StartTestInterface(graphene.Interface):
    execution_id = graphene.UUID()


class StartTest(graphene.ObjectType):
    class Meta:
        interfaces = (StartTestInterface,)


class StartTestRun(graphene.Mutation):
    class Arguments:
        conf_id = graphene.UUID(required=True)

    Output = StartTestInterface

    def mutate(self, info, conf_id, **kwargs):
        where = '(where: {id:{_eq:"' + str(conf_id) + '"}})'
        o = clients().conf.query(
            where,
        )
        return StartTest(execution_id=o[0]['id'])
