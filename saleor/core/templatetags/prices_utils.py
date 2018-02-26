from decimal import Decimal

from django.conf import settings
from django.template import Library
from django_prices.templatetags import prices_i18n


register = Library()


@register.simple_tag()
def format_price(value: Decimal, currency=None, html=False, normalize=False):
    return prices_i18n.format_price(
        value, currency=currency or settings.DEFAULT_CURRENCY,
        html=html, normalize=normalize)
