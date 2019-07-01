import graphene

from apps.bolt_api.app.appgraph import configuration, project, repository, test_creator, uploads, users, test_runs, \
    data_export, extension, argo
from apps.bolt_api.app.appgraph.project import demo
from services import gql_util


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

    # configuration extension
    testrun_extension_create = to_field(extension.Create)
    testrun_extension_create_validate = to_field(extension.CreateValidate)
    testrun_extension_update = to_field(extension.Update)
    testrun_extension_update_validate = to_field(extension.UpdateValidate)

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
    testrun_terminate = to_field(test_runs.TestrunTerminate)

    # testrun (execution) data export
    testrun_data_export = to_field(data_export.DataExportLink)

    # user management
    testrun_user_assign = to_field(users.UserAssignToProject)
    testrun_user_roles = to_field(users.UserAddRole)
    testrun_user_unassign = to_field(users.UserRemoveFromProject)
    testrun_invitation_open = to_field(users.GetProjectInvitationToken)
    testrun_invitation_register_user = to_field(users.RegisterUser)
    testrun_invitation_disable = to_field(users.DisableInvitation)

    # argo
    testrun_argo_create_execution_log = to_field(argo.CreateExecutionLog)

    # debug only
    testrun_project_purge = to_field(demo.PurgeProject)
    testrun_project_demo = to_field(demo.DemoProject)


AppSchema = graphene.Schema(
    query=TestrunQuery,
    mutation=TestrunMutations,
    types=[
        configuration.ConfigurationType,
        extension.ExtensionType,
        test_creator.TestCreatorType,
        test_runs.TestrunStartObject,
        test_runs.TestrunTerminateObject,
        test_runs.StatusResponse,
        users.UserListType,
        users.UserListItemType,
        gql_util.ValidationResponse,
        project.SummaryResponse,
    ],
    auto_camelcase=False,
)

