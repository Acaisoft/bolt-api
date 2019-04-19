import jwt
from datetime import datetime, timedelta

from services import const
from services.hasura import hce
from services.logger import setup_custom_logger

logger = setup_custom_logger(__file__)


def issue_export_token(config, scope, object_id, requested_by=None, valid_hours=24):
    """
    Creates and records an access token to all of project's execution or to a single execution's data.
    Token contains project and execution id.
    :param config: current_app.config
    :param scope: one of SCOPES
    :param object_id: either a project_id or an execution_id
    :param requested_by: uuid identifying requesting party (user id)
    :return: string: token
    """

    assert scope in const.EXPORT_SCOPE_CHOICE, f'invalid scope, must be one of {const.EXPORT_SCOPE_CHOICE}'
    storage_params = {
        'valid_hours': valid_hours,
    }

    if requested_by:
        storage_params['created_by_id'] = str(requested_by)
    else:
        logger.warn(f'issuing {scope} data token without explicit user id, no access rights validation made')

    if scope == 'project':
        storage_params['project_id'] = str(object_id)
        if requested_by:
            resp = hce(config, '''query ($eid:uuid!, $uid:uuid!) {
                project(where:{
                    is_deleted:{ _eq:false }
                    userProjects:{user_id:{ _eq:$uid }}
                }) { id }
            }''', {
                'uid': str(requested_by),
                'eid': str(object_id),
            })
            assert resp['project'], f'project not found'
    elif scope == 'execution':
        storage_params['execution_id'] = str(object_id)
        if requested_by:
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
                'eid': str(object_id),
            })
            assert resp['execution'], f'execution not found'
            storage_params['project_id'] = str(resp['execution'][0]['configuration']['project_id'])

    resp = hce(config, '''mutation ($data:execution_export_token_insert_input!) {
        insert_execution_export_token(objects:[$data]) { returning { oid } }
    }''', {'data': storage_params})

    oid = resp['insert_execution_export_token']['returning'][0][const.DATA_EXPORT_TOKEN_HANDLE_ID]
    expires = datetime.utcnow() + timedelta(hours=valid_hours)
    payload = {
        'exp': expires,
        const.DATA_EXPORT_TOKEN_HANDLE_ID: oid,
    }

    algo = config.get(const.JWT_ALGORITHM, 'HS256')
    secret = config.get(const.SECRET_KEY)
    assert secret, 'SECRET_KEY not defined'

    return jwt.encode(payload, secret, algorithm=algo).decode('utf-8')
