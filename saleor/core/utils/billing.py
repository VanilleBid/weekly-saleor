from decimal import Decimal
from typing import Union

from prices import Price

from TaxRate import RATES, CountryTax
from saleor import settings


def _get_taxed(rate: float, price: Price) -> Decimal:
    res = Decimal(float(price) * (1 + rate))
    return res


def get_tax_country_code(code, price: Union[Price, float]):
    rate = RATES.get(code, None)
    if not rate:
        rate = RATES.get(settings.DEFAULT_TAX_RATE_COUNTRY,
                         settings.FALLBACK_TAX_RATE)

    if isinstance(rate, CountryTax):
        rate = rate.rate

    if type(price) is Price:
        gross = price.gross
        currency = price.currency
    else:
        gross = price
        currency = settings.DEFAULT_CURRENCY

    taxed = _get_taxed(rate, gross)

    p = Price(gross=Decimal(taxed),
              net=gross, currency=currency)

    return p


def get_by_shipping_address(checkout):
    if checkout.shipping_address:
        country = checkout.shipping_address.country.code.upper()
        return country


def get_by_billing_address(checkout):
    if checkout.billing_address:
        country = checkout.billing_address.country.code.upper()
        return country


def get_tax_price(request, checkout=None, total=None, get_first_shipping_addr=False):
    if request:
        country = request.POST.get('country', None)
    else:
        country = None

    if checkout and not country:
        if get_first_shipping_addr:
            country = get_by_shipping_address(checkout)

            if not country:
                country = get_by_billing_address(checkout)
        else:
            country = get_by_billing_address(checkout)

    price = get_tax_country_code(country, total or checkout.get_total())
    return price


def base_template_kwargs(request, checkout, **kwargs):
    return {'taxed_total': get_tax_price(request, checkout, **kwargs)}
