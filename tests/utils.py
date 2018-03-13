from contextlib import contextmanager
from urllib.parse import urlparse

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q
from django.utils.encoding import smart_text
from PIL import Image
from io import BytesIO


def create_image():
    img_data = BytesIO()
    image = Image.new('RGB', size=(1, 1), color=(255, 0, 0, 0))
    image.save(img_data, format='JPEG')
    image_name = 'product2'
    image = SimpleUploadedFile(
        image_name + '.jpg', img_data.getvalue(), 'image/png')
    return image, image_name


def get_url_path(url):
    parsed_url = urlparse(url)
    return parsed_url.path


def get_redirect_location(response):
    # Due to Django 1.8 compatibility, we have to handle both cases
    return get_url_path(response['Location'])


def filter_products_by_attribute(queryset, attribute_id, value):
    key = smart_text(attribute_id)
    value = smart_text(value)
    in_product = Q(attributes__contains={key: value})
    in_variant = Q(variants__attributes__contains={key: value})
    return queryset.filter(in_product | in_variant)


def assert_decimal(a, b, diff=0.0001):
    assert abs(a - b) < diff


def requires_login(client):
    def _handler(fn):
        def _call(_user, *args, **kwargs):
            client.login(username=_user.email, password='password')
            return fn(_user, *args, **kwargs)
        return _call
    return _handler


@contextmanager
def set_value(o, attr, value, default=None):
    values = (value, getattr(o, attr, default))

    for i, val in enumerate(values):
        setattr(o, attr, val)
        if not i:
            yield
