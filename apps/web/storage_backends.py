from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage


class PublicMediaStorage(S3Boto3Storage):
    location = "media"
    # R2 doesn't support ACLs - all objects in R2 are private by default
    # and access is controlled via the custom domain
    default_acl = None
    file_overwrite = False
    # R2 doesn't use ACLs, so we need to disable object parameters that try to set them
    object_parameters = {}


class PrivateMediaStorage(S3Boto3Storage):
    location = "private"
    default_acl = "private"
    file_overwrite = False
    custom_domain = False


def get_private_file_storage():
    if not settings.USE_S3_MEDIA:
        return FileSystemStorage()
    else:
        return PrivateMediaStorage()
