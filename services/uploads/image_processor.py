import os

from PIL import Image
from google.cloud import storage

from services.logger import setup_custom_logger

logger = setup_custom_logger(__name__)


PROJECT_LOGO_LARGE = (810, 445)
PROJECT_LOGO_SMALL = (400, 250)
MICRO = (100, 80)
SIZES = [PROJECT_LOGO_LARGE, PROJECT_LOGO_SMALL, MICRO]
DEFAULT_SIZE = PROJECT_LOGO_SMALL


def process_image(app_config, src_object_id, dst_object_id):
    src_bucket = app_config.get('BUCKET_PRIVATE_STORAGE', None)
    dst_bucket = app_config.get('BUCKET_PUBLIC_UPLOADS', None)
    process_image_bucket(src_bucket, src_object_id, dst_bucket, dst_object_id)


def process_image_bucket(src_bucket_name, src_object_id, dst_bucket_name, dst_object_id):
    logger.info(f'processing image at {src_bucket_name}/{src_object_id}')
    src_file = f'/tmp/{src_object_id.replace("/", "_")}_original'

    try:
        gsc = storage.Client()
    except Exception as e:
        logger.error(f'cannot connect to gcs: {str(e)}')
        raise

    dst_bucket = gsc.get_bucket(dst_bucket_name)
    src_bucket = gsc.get_bucket(src_bucket_name)
    src_blob = src_bucket.get_blob(src_object_id)

    try:
        src_blob.download_to_filename(src_file)
    except Exception as e:
        logger.error(f'cannot download file locally {dst_object_id}: {str(e)}')

    for size in SIZES:
        out_file = f'/tmp/{dst_object_id.replace("/", "_")}_{size[0]}x{size[1]}'
        dst_blob_name = f'{dst_object_id}/{size[0]}x{size[1]}'

        try:
            img = Image.open(src_file)
        except Exception as e:
            logger.error(f'cannot open file {src_file}: {str(e)}')
            continue

        try:
            img.thumbnail(size)
            img.save(out_file, 'JPEG')
        except Exception as e:
            logger.error(f'cannot write thumbnail file {src_file}: {str(e)}')
            continue

        try:
            dst_blob = dst_bucket.blob(dst_blob_name)
            dst_blob.upload_from_filename(out_file, content_type='image/jpeg')
        except Exception as e:
            logger.error(f'cannot upload file {out_file}: {str(e)}')
            continue

        if size == DEFAULT_SIZE:
            # also copy this size to "root" object
            try:
                dst_blob = dst_bucket.blob(dst_object_id)
                dst_blob.upload_from_filename(out_file, content_type='image/jpeg')
                logger.info(f'uploaded {size} thumbnail to {src_bucket_name}/{dst_object_id}')
            except Exception as e:
                logger.error(f'cannot upload file {out_file} as default: {str(e)}')
                continue

        os.unlink(out_file)
        logger.info(f'uploaded {size} thumbnail to {dst_bucket_name}/{dst_blob_name}')

    if src_blob.size < 10000000:
        dst_blob_name = f'{dst_object_id}/original'
        dst_blob = dst_bucket.blob(dst_blob_name)
        logger.info(f'copying original to {dst_bucket_name}/{dst_blob_name}')
        dst_blob.upload_from_filename(src_file, content_type='image/jpeg')
    else:
        logger.warn(f'not copying original image at {src_bucket_name}/{src_object_id}: file size too large: {src_blob.size}')
    os.unlink(src_file)


if __name__ == '__main__':
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/piotr/bitbucket.org/acaisoft/bolt-api/instance/acai-bolt-356aea83d223.json'
    process_image('uploads-bolt-acaisoft', 'media.bolt.acaisoft.io', 'ffa05917-f812-4f87-9895-55e78317f100')
