from services import const
from services.hasura import hce


def get_object_public_url(object_id):
    public_bucket_name = const.BUCKET_PUBLIC_UPLOADS
    path = f'https://storage.googleapis.com/{public_bucket_name}/{object_id}'
    return path


def update_project_logo(config, object_id):
    """
    Update project's image_url column value for row id == object_id with a path to public bucket resource.
    Example image_url: https://storage.googleapis.com/media.bolt.acaisoft.io/75ad7d47-edad-4997-896f-aeb4d42701bf
    :param config: flask app.config
    :param public_bucket_name:
    :param object_id:
    :return: None
    """
    # update matching project, ignore errors or invalid objects
    path = get_object_public_url(object_id)
    resp = hce(config, '''mutation ($id:uuid!, $path:String!) {
        update_project(
            where:{ id:{ _eq:$id } }
            _set:{ image_url:$path }
        ) { affected_rows }
    }''', variable_values={
        'id': object_id,
        'path': path,
    })
