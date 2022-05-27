import uuid
from datetime import timedelta, datetime
from google.cloud import storage
from google.cloud.storage._signing import generate_signed_url_v4

from services import const
from services.logger import setup_custom_logger

logger = setup_custom_logger(__name__)


def get_upload_url(config, content_md5, content_type):
    """
    Return an upload and a (temporary) download signed url.
    :param config:
    :param content_md5:
    :param content_type:
    :return:
    """
    object_id = str(uuid.uuid4())
    project_logos_bucket = const.BUCKET_PRIVATE_STORAGE
    rsrc = f'/{project_logos_bucket}/{str(object_id)}'
    logger.info(f'generated upload link points to to https://storage.googleapis.com{rsrc}')

    upload_url = generate_signed_url_v4(
        credentials=storage.Client()._credentials,
        resource=rsrc,
        expiration=datetime.now() + timedelta(minutes=15),
        method='PUT',
        content_md5=content_md5,
        content_type=content_type,
    )

    download_url = generate_signed_url_v4(
        credentials=storage.Client()._credentials,
        resource=rsrc,
        expiration=datetime.now() + timedelta(minutes=60*24),
        method='GET'
    )

    logger.debug(f'links:\n    upload {upload_url}\n    download {download_url}')
    return upload_url, download_url
