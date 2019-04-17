import graphene

from app.appgraph import configuration, util, project, repository, test_creator, uploads, users, test_runs
from app.appgraph.project import demo


class TestrunQuery(users.UserList, test_runs.TestrunQueries, project.TestrunQueries):
    pass


def to_field(gqlClass):
    return gqlClass.Field(description=gqlClass.__doc__)


class TestrunMutations(graphene.ObjectType):
    # uploads
    testrun_upload = to_field(uploads.UploadUrl)

    # configurations
    testrun_configuration_create = to_field(configuration.Create)
    testrun_configuration_create_validate = to_field(configuration.CreateValidate)
    testrun_configuration_update = to_field(configuration.Update)
    testrun_configuration_update_validate = to_field(configuration.UpdateValidate)
    testrun_configuration_delete = to_field(configuration.Delete)

    # projects
    testrun_project_create = to_field(project.Create)
    testrun_project_create_validate = to_field(project.CreateValidate)
    testrun_project_update = to_field(project.Update)
    testrun_project_update_validate = to_field(project.UpdateValidate)
    testrun_project_delete = to_field(project.Delete)

    # repositories
    testrun_repository_create = to_field(repository.Create)
    testrun_repository_create_validate = to_field(repository.CreateValidate)
    testrun_repository_update = to_field(repository.Update)
    testrun_repository_update_validate = to_field(repository.UpdateValidate)
    testrun_repository_delete = to_field(repository.Delete)

    # test creator
    testrun_creator_create = to_field(test_creator.Create)
    testrun_creator_validate = to_field(test_creator.Validate)
    testrun_creator_update = to_field(test_creator.Update)

    # testrun management
    testrun_start = to_field(test_runs.TestrunStart)

    # user management
    testrun_user_assign = to_field(users.UserAssignToProject)
    testrun_user_roles = to_field(users.UserAddRole)
    testrun_user_unassign = to_field(users.UserRemoveFromProject)

    # debug only
    testrun_project_purge = to_field(demo.PurgeProject)
    testrun_project_demo = to_field(demo.DemoProject)


AppSchema = graphene.Schema(
    query=TestrunQuery,
    mutation=TestrunMutations,
    types=[
        configuration.ConfigurationType,
        test_creator.TestCreatorType,
        test_runs.TestrunStartObject,
        test_runs.StatusResponse,
        users.UserListType,
        users.UserListItemType,
        util.ValidationResponse,
        project.SummaryResponse,
    ],
    auto_camelcase=False,
)
