"""
Custom S3 storage backends for HandCraft.

Referenced in settings.production:
    DEFAULT_FILE_STORAGE = "utils.storage.MediaS3Storage"
    STATICFILES_STORAGE  = "utils.storage.StaticS3Storage"
"""

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaS3Storage(S3Boto3Storage):
    """S3 storage backend for user-uploaded media files."""

    bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "handcraft-media")
    location = "media"
    file_overwrite = False
    default_acl = "public-read"
    custom_domain = getattr(settings, "AWS_S3_CUSTOM_DOMAIN", None) or None
    querystring_auth = False

    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)
        params["CacheControl"] = "max-age=86400"
        return params


class StaticS3Storage(S3Boto3Storage):
    """S3 storage backend for collected static files."""

    bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "handcraft-media")
    location = "static"
    file_overwrite = True
    default_acl = "public-read"
    custom_domain = getattr(settings, "AWS_S3_CUSTOM_DOMAIN", None) or None
    querystring_auth = False

    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)
        # Static assets get a long cache TTL
        params["CacheControl"] = "max-age=2592000"
        return params
