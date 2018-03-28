import json

from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy
from impersonate.views import impersonate as orig_impersonate

from ..dashboard.views import staff_member_required
from ..homepage.models import HomePageItem
from ..product.utils import products_for_homepage, products_with_availability
from ..userprofile.models import User
from .utils.schema import get_webpage_schema


def home(request):
    products = products_for_homepage()[:8]
    featured_products = products.exists()
    blocks = HomePageItem.objects.all()
    products = products_with_availability(
        products, discounts=request.discounts, local_currency=request.currency)
    webpage_schema = get_webpage_schema(request)
    return TemplateResponse(
        request, 'home.html', {
            'parent': None,
            'products': products,
            'featured_products': featured_products,
            'blocks': blocks,
            'webpage_schema': json.dumps(webpage_schema)})


@staff_member_required
def styleguide(request):
    return TemplateResponse(request, 'styleguide.html')


def impersonate(request, uid):
    response = orig_impersonate(request, uid)
    if request.session.modified:
        msg = pgettext_lazy(
            'Impersonation message',
            'You are now logged as {}'.format(User.objects.get(pk=uid)))
        messages.success(request, msg)
    return response


def handle_404(request, exception=None):
    return TemplateResponse(request, '404.html', status=404)


def manifest(request):
    site = request.site
    ctx = {
        'description': site.settings.description,
        'name': site.name,
        'short_name': site.name}
    return TemplateResponse(
        request, 'manifest.json', ctx, content_type='application/json')


def csrf_failure(request, reason=""):
    """
    View used when request fails CSRF protection.
    """
    return TemplateResponse(request, '403_csrf.html', status=403)
