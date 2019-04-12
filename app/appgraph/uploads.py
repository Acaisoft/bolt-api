import uuid
from datetime import timedelta, datetime

import graphene
from flask import current_app

from app.appgraph.util import get_request_role_userid, OutputTypeFactory, OutputValueFromFactory
from app import const

from google.cloud import storage
from google.cloud.storage._signing import generate_signed_url


class UploadUrlReturnType(graphene.ObjectType):
    upload_url = graphene.String()
    download_url = graphene.String()
    object_id = graphene.UUID()


class UploadUrl(graphene.Mutation):
    """Generate project image upload url."""

    class Arguments:
        content_type = graphene.String(
            description='File mime type')
        content_md5 = graphene.String(
            description='Base64 encoded file content MD5 hash')
        content_length = graphene.Int(
            description='Uploaded file size, in bytes')
        object_id = graphene.UUID(
            required=False,
            description='Optional association object handle')

    Output = OutputTypeFactory(UploadUrlReturnType)

    @staticmethod
    def validate(info, content_type, content_md5, content_length, object_id=None):
        role, user_id = get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_MANAGER))

        assert content_type in const.IMAGE_CONTENT_TYPES, f'illegal content_type "{content_type}", valid choices are: {const.IMAGE_CONTENT_TYPES}'

        assert content_md5 and len(content_md5) > 10, f'invalid content_md5'

        assert content_length and content_length < const.UPLOADS_MAX_SIZE_BYTES, f'upload size exceeds allowed maximum of {const.UPLOADS_MAX_SIZE_BYTES}'

    def mutate(self, info, content_type, content_md5, content_length, object_id=None):
        # test uploading file.jpg using curl, openssl, and graphql helper cli:
        # export BASE64MD5=`cat file.jpg | openssl dgst -md5 -binary  | openssl enc -base64
        # export UPLOAD_URL=graphiql_cli.testrun_project_image_upload(content_type="image/jpeg", content_md5=$BASE64MD5, id="123").response.data.upload_url
        # curl -v -X PUT -H "Content-Type: image/jpeg" -H "Content-MD5: $BASE64MD5" -T - $UPLOAD_URL < file.jpg
        UploadUrl.validate(info, content_type, content_md5, content_length, object_id)

        if not object_id:
            object_id = uuid.uuid4()

        project_logos_bucket = current_app.config.get('BUCKET_PUBLIC_UPLOADS', 'project_logos_bucket')

        upload_url = generate_signed_url(
            credentials=storage.Client()._credentials,
            api_access_endpoint='https://storage.googleapis.com',  # change to domain configured to point to project_logos_bucket
            resource=f'/{project_logos_bucket}/temp/{str(object_id)}',
            method='PUT',
            expiration=datetime.now() + timedelta(minutes=15),
            content_md5=content_md5,
            content_type=content_type,
        )

        return OutputValueFromFactory(UploadUrl, {'returning': [{
            'object_id': str(object_id),
            'upload_url': upload_url,
            'download_url': upload_url.split('?')[0],
        }]})
