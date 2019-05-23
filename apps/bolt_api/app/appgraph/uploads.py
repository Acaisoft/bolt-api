import uuid

import graphene
from flask import current_app

from services import const, gql_util

from services.uploads.get_upload_url import get_upload_url


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
            description='Object association handle')

    Output = gql_util.OutputTypeFactory(UploadUrlReturnType)

    @staticmethod
    def validate(info, content_type, content_md5, content_length):
        role, user_id = gql_util.get_request_role_userid(info, (
        const.ROLE_ADMIN, const.ROLE_TENANT_ADMIN, const.ROLE_MANAGER))

        assert content_type in const.IMAGE_CONTENT_TYPES, f'illegal content_type "{content_type}", valid choices are: {const.IMAGE_CONTENT_TYPES}'

        assert content_md5 and len(content_md5) > 10, f'invalid content_md5'

        assert content_length and content_length < const.UPLOADS_MAX_SIZE_BYTES, f'upload size exceeds allowed maximum of {const.UPLOADS_MAX_SIZE_BYTES}'

    def mutate(self, info, content_type, content_md5, content_length, object_id):
        # test uploading file.jpg using curl, openssl, and graphql helper cli:
        # export BASE64MD5=`cat file.jpg | openssl dgst -md5 -binary  | openssl enc -base64`
        # export UPLOAD_URL=graphiql_cli.testrun_project_image_upload(content_type="image/jpeg", content_md5=$BASE64MD5, id="123").response.data.upload_url
        # curl -v -X PUT -H "Content-Type: image/jpeg" -H "Content-MD5: $BASE64MD5" -T - $UPLOAD_URL < file.jpg
        UploadUrl.validate(info, content_type, content_md5, content_length)

        upload_url, download_url = get_upload_url(current_app.config, content_md5, content_type, object_id)

        return gql_util.OutputValueFromFactory(UploadUrl, {'returning': [{
            'object_id': str(object_id),
            'upload_url': upload_url,
            'download_url': download_url,
        }]})
