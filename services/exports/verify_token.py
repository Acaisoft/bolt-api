import jwt

from services import const
from services.hasura import hce


def verify_token(config, token):
    """
    Verify token is valid, returns token payload's execution_id
    :param config: flask.app.config
    :param token: string
    :return: a two-tuple of (project_id, execution_id), execution_id may be None
    """
    payload = jwt.decode(token, config.get(const.SECRET_KEY))
    oid = payload[const.DATA_EXPORT_TOKEN_HANDLE_ID]

    resp = hce(config, '''query ($oid:Int!) {
        execution_export_token(where:{
            oid:{ _eq:$oid }
            project:{
                is_deleted:{ _eq:false }
            }
        }) {
            oid
            project_id
            execution_id
        }
    }''', {
        'oid': str(oid),
    })
    assert resp['execution_export_token'], f'export not found'

    data = resp['execution_export_token'][0]
    if data['execution_id']:
        resp = hce(config, '''query ($eid:Int!) {
            execution(where:{
                id:{ _eq:$eid }
                configuration:{
                    is_deleted:{ _eq:false }
                    project:{
                        is_deleted:{ _eq:false }
                    }
                }
            }) {
                oid
                project_id
                execution_id
            }
        }''', {
            'eid': str(data['execution_id']),
        })
        assert resp['execution'], f'exported execution not found'

    return data['project_id'], data['execution_id']
