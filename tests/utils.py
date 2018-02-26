from urllib.parse import urlparse

from django.db.models import Q
from django.utils.encoding import smart_text


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


class SetValue(object):
    def __init__(self, o, attr, value, default=None):
        self.args = (o, attr, value)
        self.old_args = (o, attr, getattr(o, attr, default))

    def __enter__(self):
        setattr(*self.args)
        return self

    def __exit__(self, *args):
        setattr(*self.old_args)
        return self
