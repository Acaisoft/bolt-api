import jwt

from app import const
from app.services.hasura import hce


def verify_token(config, token):
    """
    Verify token is valid, returns token payload's execution_id
    :param config: flask.app.config
    :param token: string
    :return: string(uuid)
    """
    payload = jwt.decode(token, config.get(const.SECRET_KEY))
    execution_id = payload['execution_id']

    resp = hce(config, '''query ($eid:uuid!) {
        execution(where:{
            id:{ _eq:$eid }
            configuration:{
                is_deleted:{ _eq:false }
                project:{
                    is_deleted:{ _eq:false }
                }
            }
        }) {
        configuration { project_id }
        }
    }''', {
        'eid': str(execution_id),
    })
    assert resp['execution'], f'execution not found'

    return execution_id
