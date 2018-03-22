from unittest.mock import Mock

import pytest
from decimal import Decimal
from django.shortcuts import reverse
from django.test import RequestFactory, Client
from prices import Price

from saleor.core.utils import (
    Country, create_superuser, get_country_by_ip, get_currency_for_country,
    random_data)
from saleor.core.utils.billing import get_tax_country_code, get_tax_price
from saleor.core.utils.warmer import CategoryWarmer, ProductWarmer, PRODUCT_IMAGE_SETS, CATEGORY_IMAGE_SETS
from saleor.core.utils.text import get_cleaner, strip_html
from saleor.discount.models import Sale, Voucher
from saleor.order.models import Order
from saleor.product.models import Product, Category, ProductImage
from saleor.shipping.models import ShippingMethod
from saleor.userprofile.models import Address, User
from tests.utils import assert_decimal, create_image

type_schema = {
    'Vegetable': {
        'category': 'Food',
        'product_attributes': {
            'Sweetness': ['Sweet', 'Sour'],
            'Healthiness': ['Healthy', 'Not really']},
        'variant_attributes': {
            'GMO': ['Yes', 'No']},
        'images_dir': 'candy/',
        'is_shipping_required': True}}


@pytest.mark.parametrize('ip_data, expected_country', [
    ({'country': {'iso_code': 'PL'}}, Country('PL')),
    ({'country': {'iso_code': 'UNKNOWN'}}, None),
    (None, None),
    ({}, None),
    ({'country': {}}, None)])
def test_get_country_by_ip(ip_data, expected_country, monkeypatch):
    monkeypatch.setattr(
        'saleor.core.utils.georeader.get',
        Mock(return_value=ip_data))
    country = get_country_by_ip('127.0.0.1')
    assert country == expected_country


@pytest.mark.parametrize('country, expected_currency', [
    (Country('PL'), 'PLN'),
    (Country('US'), 'USD'),
    (Country('GB'), 'GBP')])
def test_get_currency_for_country(country, expected_currency, monkeypatch):
    currency = get_currency_for_country(country)
    assert currency == expected_currency


def test_create_superuser(db, client):
    credentials = {'email': 'admin@example.com', 'password': 'admin'}
    # Test admin creation
    assert User.objects.all().count() == 0
    create_superuser(credentials)
    assert User.objects.all().count() == 1
    admin = User.objects.all().first()
    assert admin.is_superuser
    # Test duplicating
    create_superuser(credentials)
    assert User.objects.all().count() == 1
    # Test logging in
    response = client.post('/account/login/',
                           {'username': credentials['email'],
                            'password': credentials['password']},
                           follow=True)
    assert response.context['request'].user == admin


def test_create_shipping_methods(db):
    assert ShippingMethod.objects.all().count() == 0
    for _ in random_data.create_shipping_methods():
        pass
    assert ShippingMethod.objects.all().count() == 2


def test_create_fake_user(db):
    assert User.objects.all().count() == 0
    random_data.create_fake_user()
    assert User.objects.all().count() == 1
    user = User.objects.all().first()
    assert not user.is_superuser


def test_create_fake_users(db):
    how_many = 5
    for _ in random_data.create_users(how_many):
        pass
    assert User.objects.all().count() == 5


def test_create_address(db):
    assert Address.objects.all().count() == 0
    random_data.create_address()
    assert Address.objects.all().count() == 1


def test_create_attribute(db):
    data = {'slug': 'best_attribute', 'name': 'Best attribute'}
    attribute = random_data.create_attribute(**data)
    assert attribute.name == data['name']
    assert attribute.slug == data['slug']


def test_create_product_types_by_schema(db):
    product_type = random_data.create_product_types_by_schema(
        type_schema)[0][0]
    assert product_type.name == 'Vegetable'
    assert product_type.product_attributes.count() == 2
    assert product_type.variant_attributes.count() == 1
    assert product_type.is_shipping_required


def test_create_products_by_type(db):
    assert Product.objects.all().count() == 0
    how_many = 5
    product_type = random_data.create_product_types_by_schema(
        type_schema)[0][0]
    random_data.create_products_by_type(
        product_type, type_schema['Vegetable'], '/',
        how_many=how_many, create_images=False)
    assert Product.objects.all().count() == how_many


def test_create_fake_order(db):
    for _ in random_data.create_shipping_methods():
        pass
    for _ in random_data.create_users(3):
        pass
        random_data.create_products_by_schema('/', 10, False)
    how_many = 5
    for _ in random_data.create_orders(how_many):
        pass
    assert Order.objects.all().count() == 5


def test_create_product_sales(db):
    how_many = 5
    for _ in random_data.create_product_sales(how_many):
        pass
    assert Sale.objects.all().count() == 5


def test_create_vouchers(db):
    assert Voucher.objects.all().count() == 0
    for _ in random_data.create_vouchers():
        pass
    assert Voucher.objects.all().count() == 2


def test_manifest(client, site_settings):
    response = client.get(reverse('manifest'))
    assert response.status_code == 200
    content = response.json()
    assert content['name'] == site_settings.site.name
    assert content['short_name'] == site_settings.site.name
    assert content['description'] == site_settings.description


def test_utils_get_cleaner_invalid_parameters():
    with pytest.raises(ValueError):
        get_cleaner(bad=True)


def test_utils_strip_html():
    base_text = ('<p>Hello</p>'
                 '\n\n'
                 '\t<b>World</b>')
    text = strip_html(base_text, strip_whitespace=True)
    assert text == 'Hello World'


def test_get_tax_country_code():
    price, rate = get_tax_country_code('AT', Price(Decimal(10.0)))

    assert price.gross == Decimal(12)
    assert rate == 0.20

    price, rate = get_tax_country_code('AT', Decimal(10.0))
    assert price.gross == Decimal(12)
    assert rate == 0.20


def test_get_tax_price(order_with_lines: Order, billing_address):
    order = order_with_lines
    order.billing_address = billing_address
    order.shipping_address = shipping_address = Address.objects.create(
        first_name='John', last_name='Doe',
        company_name='Mirumee Software',
        street_address_1='Tęczowa 7',
        city='Wrocław',
        postal_code='53-601',
        country='PL',
        phone='+48713988102')

    request_factory = RequestFactory()
    order_total = order.get_total()

    croatia_tax_rate = 0.25
    poland_tax_rate = 0.23
    default_tax_rate = 0.20

    croatia_taxed_price = order_total.gross * Decimal(1 + croatia_tax_rate)
    poland_taxed_price = order_total.gross * Decimal(1 + poland_tax_rate)

    croatia_taxed_price_10usd = Decimal(10.0) * Decimal(1 + croatia_tax_rate)
    default_taxed_price_10usd = Decimal(10.0) * Decimal(1 + default_tax_rate)

    requests = (
        (request_factory.post('/test_HR', {'country': 'HR'}),
         croatia_taxed_price,
         croatia_tax_rate,
         croatia_taxed_price_10usd),

        (request_factory.post('/test_default_missing', {}),
         poland_taxed_price,
         poland_tax_rate,
         default_taxed_price_10usd),

        (request_factory.post('/test_default_None'),
         poland_taxed_price,
         poland_tax_rate,
         default_taxed_price_10usd)
    )

    for rq, expected_price, expected_rate, expected_price_10usd in requests:
        price, rate = get_tax_price(rq, checkout=order)
        assert rate == expected_rate
        assert_decimal(price.gross, expected_price)

        price, rate = get_tax_price(rq, total=10)
        expected_rate = (float(expected_price_10usd) - 10) / 10.0
        assert_decimal(rate, expected_rate)
        assert_decimal(price.gross, expected_price_10usd)

    shipping_address.country = Country('HR')

    price, rate = get_tax_price(None, checkout=order, get_first_shipping_addr=True)
    assert rate == 0.25
    assert_decimal(price.gross, croatia_taxed_price)

    price, rate = get_tax_price(None, checkout=order, get_first_shipping_addr=False)
    assert rate == 0.23
    assert_decimal(price.gross, poland_taxed_price)

    order.shipping_address = None
    price, rate = get_tax_price(None, checkout=order, get_first_shipping_addr=True)
    assert rate == 0.23
    assert_decimal(price.gross, poland_taxed_price)


def test_get_robots_txt(client):
    response = client.get('/robots.txt')
    robots_txt = b'User-agent: *\nDisallow: /'
    assert response.status_code == 200
    assert response.get('Content-Type').startswith('text/plain')
    assert client.get('/robots.txt').content.strip() == robots_txt


def test_csrf_view():
    url = reverse('account_signup')
    client = Client(enforce_csrf_checks=True)
    response = client.post(url)
    assert response.status_code == 403


def test_warmer(product_in_stock, product_type):
    Category.objects.create(name='b', slug='b')
    category = Category.objects.create(name='c', slug='c', image=create_image()[0])
    product = Product.objects.create(name='b', price=Decimal('1.00'), product_type=product_type, category=category)

    product_warmer = ProductWarmer.all()
    category_warmer = CategoryWarmer.all()

    assert category_warmer._wrapper.query_set.count() == 3
    assert product_warmer._wrapper.query_set.count() == 0

    assert category_warmer() == 1 * len(CATEGORY_IMAGE_SETS)
    assert product_warmer() == 0

    for i in range(1, 3):
        ProductImage.objects.create(product=product, image=create_image()[0])
        assert ProductWarmer.all()._wrapper.query_set.count() == i
        assert ProductWarmer.all()() == len(PRODUCT_IMAGE_SETS)


def test_home_view_featured_products(client: Client, product_in_stock: Product):
    url = reverse('home')
    expected_html = b'<div class="home__featured">'

    product_in_stock.is_featured = False
    product_in_stock.save()

    def _get():
        _response = client.get(url)
        assert _response.status_code == 200
        return _response.content

    assert expected_html not in _get()

    product_in_stock.is_featured = True
    product_in_stock.save()

    assert expected_html in _get()
