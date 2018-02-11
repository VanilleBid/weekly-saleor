from typing import Union

from decimal import Decimal
from prices import Price

from TaxRate import RATES
from saleor import settings


def get_tax_country_code(code, price: Union[Price, float]):
    rate = RATES.get(code, None)
    if not rate:
        rate = RATES[settings.DEFAULT_TAX_RATE_COUNTRY]

    if type(price) is Price:
        gross = price.gross
    else:
        gross = price

    taxed_price = rate.get_taxed(gross)
    p = Price(gross=Decimal(taxed_price), net=gross, currency=price.currency)

    return p


def get_tax_price(request, checkout=None, total=None):
    if request:
        country = request.POST.get('country', None)
    else:
        country = None

    if checkout:
        if not country and checkout.billing_address:
            country = checkout.billing_address.country.code.upper()

        if not country and checkout.shipping_address:
            country = checkout.shipping_address.country.code.upper()

    price = get_tax_country_code(country, total or checkout.get_total())
    return price


def base_template_kwargs(request, checkout):
    return {'taxed_total': get_tax_price(request, checkout)}

