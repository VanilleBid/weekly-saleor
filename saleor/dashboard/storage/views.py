from pathlib import Path

from django.conf import settings
from django.http import Http404
from django.template.response import TemplateResponse
from django.utils.functional import LazyObject

from storages.backends.s3boto3 import S3Boto3Storage

from saleor.dashboard.views import staff_member_required
from django.core.files.storage import get_storage_class


def _storage(cls) -> S3Boto3Storage:
    return cls()


@_storage
class MediaStorage(LazyObject):
    def _setup(self):
        self._wrapped = get_storage_class(settings.THUMBNAIL_DEFAULT_STORAGE)()


@_storage
class StaticStorage(LazyObject):
    def _setup(self):
        self._wrapped = get_storage_class(settings.STATICFILES_STORAGE)()


def requires_s3_storage(storage):
    def _requires_s3_storage(view):
        if isinstance(storage, S3Boto3Storage):
            wrapper = view
        else:
            def wrapper(*args, **kwargs):
                raise Http404('No {} bucket.'.format(storage))
        return wrapper
    return _requires_s3_storage


@requires_s3_storage(MediaStorage)
@staff_member_required
def media_bucket(request):
    real_root = Path(settings.MEDIA_ROOT)

    ctx = {
        'bucket_name': 'media',
        'missing_files': [],
        'to_remove_files': []
    }
    return TemplateResponse(request, 'dashboard/storage/base.html', ctx)


@requires_s3_storage(StaticStorage)
@staff_member_required
def static_bucket(request):
    real_root = Path(settings.STATIC_ROOT)

    ctx = {
        'bucket_name': 'static',
        'missing_files': [],
        'to_remove_files': []
    }
    return TemplateResponse(request, 'dashboard/storage/base.html', ctx)
