import graphene

from app.appgraph import configuration, testrun, util, project, repository, test_creator
from app.appgraph import oauth


class TestrunQuery(oauth.QueryOauth, testrun.TestrunQueries):
    pass


def to_field(gqlClass):
    return gqlClass.Field(description=gqlClass.__doc__)


class TestrunMutations(graphene.ObjectType):
    testrun_configuration_create = to_field(configuration.Create)
    testrun_configuration_create_validate = to_field(configuration.CreateValidate)
    testrun_configuration_update = to_field(configuration.Update)
    testrun_configuration_update_validate = to_field(configuration.UpdateValidate)
    testrun_project_create = to_field(project.Create)
    testrun_project_validate = to_field(project.Validate)
    testrun_repository_create = to_field(repository.Create)
    testrun_repository_validate = to_field(repository.Validate)
    testrun_creator_create = to_field(test_creator.Create)
    testrun_creator_validate = to_field(test_creator.Validate)
    testrun_start = to_field(testrun.TestrunStart)


AppSchema = graphene.Schema(
    query=TestrunQuery,
    mutation=TestrunMutations,
    types=[
        configuration.ConfigurationType,
        project.ProjectType,
        repository.RepositoryType,
        test_creator.TestCreatorType,
        oauth.Oauth,
        oauth.OauthAuthtoken,
        testrun.TestrunStartObject,
        testrun.StatusResponse,
        util.ValidationResponse,
    ],
    auto_camelcase=False,
)
