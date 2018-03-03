import pytest
from django.test import RequestFactory

import saleor.dashboard.storage.views as storage_views

from importlib import reload

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import Http404
from django.urls import reverse
from storages.backends.s3boto3 import S3Boto3Storage
from ..utils import SetValue


S3_STORAGE_IMPORT_NAME = 'saleor.core.storages.S3MediaStorage'


class StorageViewEditor(SetValue):
    def requires_reload(fn):
        def _wrapper(*args, **kwargs):
            ret = fn(*args, **kwargs)
            reload(storage_views)
            return ret
        return _wrapper

    @requires_reload
    def __enter__(self):
        return super(self.__class__, self).__enter__()

    @requires_reload
    def __exit__(self, *args):
        return super(self.__class__, self).__exit__()


def test_requires_s3_storage():
    HANDLING_VIEW = 123

    s3_storage = S3Boto3Storage()
    file_storage = FileSystemStorage()

    def _run_test(_storage):
        view = storage_views.requires_s3_storage(_storage)(HANDLING_VIEW)
        return view

    assert _run_test(s3_storage) == HANDLING_VIEW

    file_view = _run_test(file_storage)
    assert file_view != HANDLING_VIEW

    with pytest.raises(Http404):
        file_view()


def test_no_setup(client):
    """
    Default settings are not configured for S3 storage,
    views should return 404.
    """
    storage_types = ('media', 'static')

    for storage_type in storage_types:
        url = reverse('dashboard:bucket-%s' % storage_type)
        response = client.get(url)
        response.status_code = 404


def test_media_bucket():
    with StorageViewEditor(
            settings, 'THUMBNAIL_DEFAULT_STORAGE', S3_STORAGE_IMPORT_NAME):
        request = RequestFactory()
        response = storage_views.media_bucket(request)
        assert b'media bucket' in response.content


def test_static_bucket():
    with StorageViewEditor(
            settings, 'STATICFILES_STORAGE', S3_STORAGE_IMPORT_NAME):
        request = RequestFactory()
        response = storage_views.static_bucket(request)
        assert b'static bucket' in response.content
