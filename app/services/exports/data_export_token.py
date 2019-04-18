import jwt
from datetime import datetime, timedelta

from app import const
from app.logger import setup_custom_logger
from app.services.hasura import hce


logger = setup_custom_logger(__file__)


def issue_export_token(config, execution_id, requested_by=None, valid_hours=24):
    """
    Creates and records an access token to project's execution data.
    Token contains project and execution id.
    :param config: current_app.config
    :param execution_id: execution results to grant access to
    :param requested_by: uuid identifying requesting party (user id)
    :return: string: token
    """
    project_id = None
    storage_params = {
        'execution_id': str(execution_id),
    }

    # verify access right if requesting user is defined
    if requested_by:
        storage_params['created_by_id'] = str(requested_by)
        resp = hce(config, '''query ($eid:uuid!, $uid:uuid!) {
            execution(where:{
                id:{ _eq:$eid }
                configuration:{
                    is_deleted:{ _eq:false }
                    project:{
                        is_deleted:{ _eq:false }
                        userProjects:{user_id:{ _eq:$uid }}
                    }
                }
            }) {
            configuration { project_id }
            }
        }''', {
            'uid': str(requested_by),
            'eid': str(execution_id),
        })
        assert resp['execution'], f'execution not found'
        project_id = resp['execution'][0]['configuration']['project_id']

    else:
        logger.warn('issuing data token without explicit user id, no access rights validation made')

    expires = datetime.utcnow() + timedelta(hours=valid_hours)
    payload = {
        'exp': expires,
        'execution_id': str(execution_id),
        'project_id': str(project_id),
        'created_by_id': str(requested_by),
    }

    algo = config.get(const.JWT_ALGORITHM, 'HS256')
    secret = config.get(const.SECRET_KEY)
    assert secret, 'SECRET_KEY not defined'
    token = jwt.encode(payload, secret, algorithm=algo).decode('utf-8')

    storage_params['token'] = token

    hce(config, '''mutation ($data:execution_export_token_insert_input!) {
        insert_execution_export_token(objects:[$data]) { affected_rows }
    }''', {'data': storage_params})

    return token
