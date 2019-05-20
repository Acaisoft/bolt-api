from datetime import timedelta, datetime
from google.cloud import storage
from google.cloud.storage._signing import generate_signed_url_v4


def get_upload_url(config, content_md5, content_type, object_id):
    project_logos_bucket = config.get('BUCKET_PUBLIC_UPLOADS', 'project_logos_bucket')
    rsrc = f'/{project_logos_bucket}/temp/{str(object_id)}'
    print(f'uploading to {rsrc}')

    upload_url = generate_signed_url_v4(
        credentials=storage.Client()._credentials,
        resource=rsrc,
        expiration=datetime.now() + timedelta(minutes=15),
        method='PUT',
        content_md5=content_md5,
        content_type=content_type,
    )

    return upload_url
