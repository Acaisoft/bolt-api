import graphene
from app import const


class RepositoryParameterInterface(graphene.InputObjectType):
    name = graphene.String()
    repository_url = graphene.String()
    project_id = graphene.UUID()
    type_slug = graphene.String(description=f'Configuration type: "{const.TESTTYPE_CHOICE}"')


class RepositoryInterface(graphene.Interface):
    id = graphene.UUID()
    name = graphene.String(
        description='Name')
    repository_url = graphene.String(
        description='Repository address')
    project_id = graphene.UUID(
        description='Repository project')
    type_slug = graphene.String(
        description=f'Configuration type: "{const.TESTTYPE_CHOICE}"')
