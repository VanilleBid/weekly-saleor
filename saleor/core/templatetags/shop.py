from django.template import Library
from django.utils.http import urlencode

register = Library()


@register.simple_tag(takes_context=True)
def get_sort_by_url(context, field, descending=False):
    request = context['request']
    request_get = request.GET.dict()
    if descending:
        request_get['sort_by'] = '-' + field
    else:
        request_get['sort_by'] = field
    return '%s?%s' % (request.path, urlencode(request_get))


@register.filter
def length_gt(value, arg):
    """Returns a boolean of whether the value is greater than an argument."""
    return len(value) > int(arg)
