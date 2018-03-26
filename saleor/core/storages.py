from S3CachedStorage.backends.S3CachedBucket import S3CachedBucket
from django.conf import settings
from django.contrib.staticfiles.storage import StaticFilesStorage
from storages.backends.s3boto3 import S3Boto3Storage


class S3MediaStorage(S3Boto3Storage):
    def __init__(self, *args, **kwargs):
        self.bucket_name = settings.AWS_MEDIA_BUCKET_NAME

        if settings.AWS_MEDIA_CUSTOM_DOMAIN:
            self.custom_domain = settings.AWS_MEDIA_CUSTOM_DOMAIN
        super().__init__(*args, **kwargs)


class S3PrivateStorage(S3CachedBucket):
    STORAGE_NAME = 'PRIVATE_STORAGE'

    def __init__(self, *args, **kwargs):
        self.bucket_name = settings.PRIVATE_STORAGE_S3_STORAGE_BUCKET_NAME
        super().__init__(*args, **kwargs)


class PrivateStorageLocalOnly(StaticFilesStorage):
    def __init__(self, *args, **kwargs):
        location = settings.PRIVATE_STORAGE_S3_STORAGE_BACKEND_CACHE_DIR
        super(PrivateStorageLocalOnly, self).__init__(location, *args, **kwargs)
