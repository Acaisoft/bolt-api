import graphene

from app.appgraph import configuration, testrun, util, project, repository, test_creator
from app.appgraph import oauth


class TestrunQuery(oauth.QueryOauth, testrun.TestrunQueries):
    pass


def to_field(gqlClass):
    return gqlClass.Field(description=gqlClass.__doc__)


class TestrunMutations(graphene.ObjectType):
    # configurations
    testrun_configuration_create = to_field(configuration.Create)
    testrun_configuration_create_validate = to_field(configuration.CreateValidate)
    testrun_configuration_update = to_field(configuration.Update)
    testrun_configuration_update_validate = to_field(configuration.UpdateValidate)

    # projects
    testrun_project_create = to_field(project.Create)
    testrun_project_create_validate = to_field(project.CreateValidate)
    testrun_project_update = to_field(project.Update)
    testrun_project_update_validate = to_field(project.UpdateValidate)
    testrun_project_image_upload = to_field(project.ImageUploadUrl)

    # repositories
    testrun_repository_create = to_field(repository.Create)
    testrun_repository_create_validate = to_field(repository.CreateValidate)
    testrun_repository_update = to_field(repository.Update)
    testrun_repository_update_validate = to_field(repository.UpdateValidate)

    # test creator
    testrun_creator_create = to_field(test_creator.Create)
    testrun_creator_validate = to_field(test_creator.Validate)

    # testrun management
    testrun_start = to_field(testrun.TestrunStart)

    # debug only
    testrun_project_purge = to_field(project.PurgeProject)
    testrun_project_demo = to_field(project.DemoProject)


AppSchema = graphene.Schema(
    query=TestrunQuery,
    mutation=TestrunMutations,
    types=[
        configuration.ConfigurationType,
        test_creator.TestCreatorType,
        oauth.Oauth,
        oauth.OauthAuthtoken,
        testrun.TestrunStartObject,
        testrun.StatusResponse,
        util.ValidationResponse,
    ],
    auto_camelcase=False,
)
