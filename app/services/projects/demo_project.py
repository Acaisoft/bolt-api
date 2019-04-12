import threading

from gql import gql

from app import const
from app.hasura_client import hasura_client
from app.logger import setup_custom_logger
from app.services.user_management import user_management

logger = setup_custom_logger(__name__)


SMOKE_TEST_REPO = 'git@bitbucket.org:acaisoft/bolt-sample-load.git'
SMOKE_TEST_TARGET = 'https://test-target.dev.bolt.acaisoft.io'


example_request_result = [{"Min response time":"146","Average Content Size":"12","# failures":"0","Median response time":"150","Name":"/api/","Method":"GET","Max response time":"363","Average response time":"176","Requests/s":"1.13","# requests":"11"},{"Min response time":"0","Average Content Size":"0","# failures":"7","Median response time":"0","Name":"/api/echo/hello","Method":"GET","Max response time":"0","Average response time":"0","Requests/s":"0.00","# requests":"0"},{"Min response time":"0","Average Content Size":"0","# failures":"2","Median response time":"0","Name":"/api/error/400or500","Method":"GET","Max response time":"0","Average response time":"0","Requests/s":"0.00","# requests":"0"},{"Min response time":"0","Average Content Size":"0","# failures":"6","Median response time":"0","Name":"/api/error/401","Method":"GET","Max response time":"0","Average response time":"0","Requests/s":"0.00","# requests":"0"},{"Min response time":"0","Average Content Size":"0","# failures":"8","Median response time":"0","Name":"/api/error/404","Method":"GET","Max response time":"0","Average response time":"0","Requests/s":"0.00","# requests":"0"},{"Min response time":"0","Average Content Size":"0","# failures":"4","Median response time":"0","Name":"/api/random","Method":"GET","Max response time":"0","Average response time":"0","Requests/s":"0.00","# requests":"0"},{"Min response time":"0","Average Content Size":"0","# failures":"4","Median response time":"0","Name":"/api/send","Method":"POST","Max response time":"0","Average response time":"0","Requests/s":"0.00","# requests":"0"},{"Min response time":"146","Average Content Size":"12","# failures":"31","Median response time":"150","Name":"Total","Method":"None","Max response time":"363","Average response time":"176","Requests/s":"1.13","# requests":"11"}]
example_distribution_result = [{"90%":"210","100%":"360","80%":"170","99%":"360","50%":"150","95%":"360","98%":"360","Name":"GET /api/","75%":"170","66%":"170","# requests":"11"},{"90%":"N/A","100%":"N/A","80%":"N/A","99%":"N/A","50%":"N/A","95%":"N/A","98%":"N/A","Name":"/api/echo/hello","75%":"N/A","66%":"N/A","# requests":"0"},{"90%":"N/A","100%":"N/A","80%":"N/A","99%":"N/A","50%":"N/A","95%":"N/A","98%":"N/A","Name":"/api/error/400or500","75%":"N/A","66%":"N/A","# requests":"0"},{"90%":"N/A","100%":"N/A","80%":"N/A","99%":"N/A","50%":"N/A","95%":"N/A","98%":"N/A","Name":"/api/error/401","75%":"N/A","66%":"N/A","# requests":"0"},{"90%":"N/A","100%":"N/A","80%":"N/A","99%":"N/A","50%":"N/A","95%":"N/A","98%":"N/A","Name":"/api/error/404","75%":"N/A","66%":"N/A","# requests":"0"},{"90%":"N/A","100%":"N/A","80%":"N/A","99%":"N/A","50%":"N/A","95%":"N/A","98%":"N/A","Name":"/api/random","75%":"N/A","66%":"N/A","# requests":"0"},{"90%":"N/A","100%":"N/A","80%":"N/A","99%":"N/A","50%":"N/A","95%":"N/A","98%":"N/A","Name":"/api/send","75%":"N/A","66%":"N/A","# requests":"0"},{"90%":"210","100%":"360","80%":"170","99%":"360","50%":"150","95%":"360","98%":"360","Name":"Total","75%":"170","66%":"170","# requests":"11"}]
example_test_creator_data = '''{"global_headers":{"HASURA_GRAPHQL_JWT_SECRET":"secret-key","Token":"Bearer ${token}"},"on_start":{"endpoints":[{"actions":[{"variable_path":"auth.token","location":"response","variable_name":"token","action_type":"set_variable"},{"variable_path":"auth.type","location":"response","variable_name":"token_type","action_type":"set_variable"}],"url":"/auth-response","payload":{"username":"my_user","password":"my_password"},"name":"Auth","method":"post"}]},"endpoints":[{"url":"/user/info","payload":{"my_token_type":"JWT","my_token":"My token is ${token}"},"asserts":[{"value":"200","assert_type":"response_code","message":"Eh... Not 200"}],"headers":{"Content-Type":"application/json","Test-Data-Key":"Test data value"},"name":"User info","method":"get","task_value":1},{"url":"/user/save","payload":{"my_name":"Hello, my name is ${name}","my_token_type":"JWT"},"asserts":[{"value":"200","assert_type":"response_code","message":"Eh... Not 200"}],"name":"User save","method":"post","task_value":2},{"url":"/user/delete","asserts":[{"value":"204","assert_type":"response_code","message":"Status code is not 204 for delete"}],"headers":{"TokenType":"token ${token_type}"},"name":"User delete","method":"delete","task_value":3}],"test_type":"set"}'''


def setup_demo_project(config, name, req_user_id, req_user_email):
    project_logo = 'https://storage.googleapis.com/media.bolt.acaisoft.io/project_logos/d85d29e5-8204-46a7-8218-40bdcf68c978'

    assert not all((req_user_id, req_user_email)), 'must provide one of user_id, user_email'
    assert any((req_user_id, req_user_email)), 'must provide either user_id or user_email'

    gclient = hasura_client(config)

    # create project
    logger.info(f'creating project {name}')
    proj_resp = gclient.execute(gql('''mutation ($name:String!, $logo:String!) {
        testrun_project_create (name:$name, description:"demo project", image_url:$logo) { returning {id} }
    }'''), {'logo': project_logo, 'name': name})
    project_id = proj_resp['testrun_project_create']['returning'][0]['id']

    if req_user_email:
        # create and assign user
        user_management.user_create(req_user_email, project_id, const.ROLE_READER)
    elif req_user_id:
        # assign user to project
        logger.info(f'assigning user {req_user_id} to project {project_id}')
        gclient.execute(gql('''mutation ($id:uuid!, $user_id:uuid!) {
            insert_user_project (objects:[{id:$id,, project_id:$id, user_id:$user_id}]) {affected_rows}
        }'''), {'id': project_id, 'user_id': req_user_id})

    threading.Thread(target=fill_in_project, args=(config, name, project_id)).start()

    logger.info('setup_demo_project finished')
    return project_id


def fill_in_project(config, name, project_id):
    logger.info('fill_in_project starting')

    gclient = hasura_client(config)

    # create a repository test source
    logger.info('creating a repository test source')
    resp = gclient.execute(gql('''mutation ($name:String!, $id:UUID!) {
    testrun_repository_create (
        name:$name
        project_id:$id
        repository_url:"%(SMOKE_TEST_REPO)s"
        type_slug:"load_tests"
    ) { returning { id } }
    }''' % {
        'SMOKE_TEST_REPO': SMOKE_TEST_REPO,
    }), {
        'id': project_id,
        'name': name + ' repository',
    })
    testsource_repo_id = resp['testrun_repository_create']['returning'][0]['id']

    # create a creator test source
    logger.info('creating a test_creator test source')
    resp = gclient.execute(gql('''mutation ($name:String!, $id:UUID!, $test_creator_data:String!) {
    testrun_creator_create (
        name:$name
        project_id:$id
        max_wait:200
        min_wait:100
        data:$test_creator_data
        type_slug:"load_tests"
    ) { returning { id } }
    }'''), {
        'id': project_id,
        'name': name + ' creator',
        'test_creator_data': example_test_creator_data,
    })
    testsource_creator_id = resp['testrun_creator_create']['returning'][0]['id']

    # create a repository configuration with master/slave setup
    logger.info('creating a repository test configuration')
    resp = gclient.execute(gql('''mutation ($name:String!, $id:UUID!, $testsource_repo_id:UUID!) {
    testrun_configuration_create(
        name:$name
        project_id:$id
        type_slug:"load_tests"
        test_source_id:$testsource_repo_id
        configuration_parameters:[{
            parameter_slug:"load_tests_host"
            value:"%(SMOKE_TEST_TARGET)s"
        }, {
            parameter_slug:"load_tests_duration"
            value:"30"
        }, {
            parameter_slug:"load_tests_users"
            value:"%(load_tests_users)s"
        }]) { returning { id } }
    }''' % {
        'SMOKE_TEST_TARGET': SMOKE_TEST_TARGET,
        'load_tests_users': int(const.TESTRUN_MAX_USERS_PER_INSTANCE * 2),
    }), {
        'id': project_id,
        'name': name + ' repo',
        'testsource_repo_id': testsource_repo_id,
    })
    configuration_repo_id = resp['testrun_configuration_create']['returning'][0]['id']

    # create a creator configuration
    logger.info('creating a test_creator test configuration')
    resp = gclient.execute(gql('''mutation ($name:String!, $id:UUID!, $testsource_creator_id:UUID!) {
    testrun_configuration_create(
        name:$name
        project_id:$id
        type_slug:"load_tests"
        test_source_id:$testsource_creator_id
        configuration_parameters:[{
            parameter_slug:"load_tests_host"
            value:"%(SMOKE_TEST_TARGET)s"
        }]) { returning { id } }
    }''' % {
        'SMOKE_TEST_TARGET': SMOKE_TEST_TARGET,
    }), {
        'id': project_id,
        'name': name + ' creator',
        'testsource_creator_id': testsource_creator_id,
    })
    configuration_creator_id = resp['testrun_configuration_create']['returning'][0]['id']

    # create an undefined configuration
    logger.info('creating an undefined test configuration')
    gclient.execute(gql('''mutation ($name:String!, $id:UUID!) {
    testrun_configuration_create(
        name:$name
        project_id:$id
        type_slug:"load_tests"
        configuration_parameters:[{
            parameter_slug:"load_tests_host"
            value:"%(SMOKE_TEST_TARGET)s"
        }]) { returning { id } }
    }''' % {
        'SMOKE_TEST_TARGET': SMOKE_TEST_TARGET,
    }), {
        'id': project_id,
        'name': name + ' undefined source',
    })

    # start both configurations
    logger.info('starting tests of repository configuration')
    resp = gclient.execute(gql('''mutation ($id:UUID!) {
    testrun_start( conf_id:$id ) { execution_id }
    }'''), {
        'id': configuration_repo_id,
    })
    execution_repo_id = resp['testrun_start']['execution_id']

    logger.info('starting tests of test_creator configuration')
    resp = gclient.execute(gql('''mutation ($id:UUID!) {
    testrun_start( conf_id:$id ) { execution_id }
    }'''), {
        'id': configuration_creator_id,
    })
    execution_creator_id = resp['testrun_start']['execution_id']

    # check status on both executions
    logger.info('checking status of executions')
    resp = gclient.execute(gql('''query ($exid1:UUID!, $exid2:UUID!) {
        status1: testrun_status(execution_id:$exid1) { status }
        status2: testrun_status(execution_id:$exid2) { status }
    }'''), {
        'exid1': execution_repo_id,
        'exid2': execution_creator_id,
    })
    logger.info(f'executions: {str(resp)}')

    logger.info('fill_in_project done')
    return project_id
