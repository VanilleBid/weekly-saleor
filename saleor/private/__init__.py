from django.conf import settings
from django.core.files.storage import get_storage_class

private_storage = get_storage_class(settings.PRIVATE_STORAGE_S3_STORAGE)()
