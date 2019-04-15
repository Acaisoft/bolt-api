from app.services.hasura import hce
from app.logger import setup_custom_logger

logger = setup_custom_logger(__name__)


def teardown(config, project_name, project_id):
    """
    Perform complete project data teardown.
    TODO: clean up any referenced jobs through bolt-deployer.
    Provide with either project_name (accepts sql wildcards) or a project_id.
    """
    assert not all((project_id, project_name)), f'use either project_name or project_id, not both'
    assert any((project_id, project_name)), f'either project_name or project_id must be provided'

    if project_name:
        projects = hce(config,
            '''query ($name:String!) { project(where:{name:{_ilike:$name}}) { id } }''',
            variable_values={'name': project_name}
        )
        project_ids_list = [str(x['id']) for x in projects['project']]
    elif project_id:
        project_ids_list = [str(project_id)]
    else:
        raise RuntimeError('either project_name or project_id must be provided')

    logger.info(f'deleting {len(project_ids_list)} projects')

    hce(config, '''mutation ($projIds:[uuid!]!) {
        delete_configuration_parameter (where:{configuration:{project_id:{_in:$projIds}}}) {affected_rows}
        delete_result_error (where:{execution:{configuration:{project_id:{_in:$projIds}}}}) {affected_rows}
        delete_result_distribution (where:{execution:{configuration:{project_id:{_in:$projIds}}}}) {affected_rows}
        delete_result_aggregate (where:{execution:{configuration:{project_id:{_in:$projIds}}}}) {affected_rows}
        delete_execution_instance (where:{execution:{configuration:{project_id:{_in:$projIds}}}}) {affected_rows}
        delete_execution (where:{configuration:{project_id:{_in:$projIds}}}) {affected_rows}
        delete_configuration (where:{project_id:{_in:$projIds}}) {affected_rows}
        delete_test_source(where:{project_id:{_in:$projIds}}) { affected_rows }
        delete_test_creator (where:{project_id:{_in:$projIds}}) {affected_rows}
        delete_repository (where:{project_id:{_in:$projIds}}) {affected_rows}
        delete_user_project (where:{project_id:{_in:$projIds}}) {affected_rows}
        delete_project(where:{id:{_in:$projIds}}) {affected_rows}
    }''', variable_values={'projIds': project_ids_list})

    logger.info(f'success: {project_ids_list}')

    return project_ids_list
