from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pytest
from django.test import Client
from freezegun import freeze_time
from prices import FixedDiscount, FractionalDiscount, Price

from saleor.discount import (
    DiscountValueType, VoucherApplyToProduct, VoucherType)
from saleor.discount.forms import CheckoutDiscountForm
from saleor.discount.models import NotApplicable, Sale, Voucher
from saleor.discount.utils import (
    decrease_voucher_usage, increase_voucher_usage)
from saleor.product.models import Product, ProductVariant, StockLocation, Stock, Category
from saleor.userprofile.models import User
from tests.utils import json_variant_details


@pytest.mark.parametrize('limit, value', [
    (Price(5, currency='USD'), Price(10, currency='USD')),
    (Price(10, currency='USD'), Price(10, currency='USD'))])
def test_valid_voucher_limit(settings, limit, value):
    voucher = Voucher(
        code='unique', type=VoucherType.SHIPPING,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=Price(10, currency='USD'),
        limit=limit)
    voucher.validate_limit(value)


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_variant_discounts(product_in_stock):
    variant = product_in_stock.variants.get()
    low_discount = Sale.objects.create(
        type=DiscountValueType.FIXED,
        value=5)
    low_discount.products.add(product_in_stock)
    discount = Sale.objects.create(
        type=DiscountValueType.FIXED,
        value=8)
    discount.products.add(product_in_stock)
    high_discount = Sale.objects.create(
        type=DiscountValueType.FIXED,
        value=50)
    high_discount.products.add(product_in_stock)
    final_price = variant.get_price_per_item(
        discounts=Sale.objects.all())
    assert final_price.gross == 0
    applied_discount = final_price.history.right
    assert isinstance(applied_discount, FixedDiscount)
    assert applied_discount.amount.gross == 50


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_percentage_discounts(product_in_stock):
    variant = product_in_stock.variants.get()
    discount = Sale.objects.create(
        type=DiscountValueType.PERCENTAGE,
        value=50)
    discount.products.add(product_in_stock)
    final_price = variant.get_price_per_item(discounts=[discount])
    assert final_price.gross == 5
    applied_discount = final_price.history.right
    assert isinstance(applied_discount, FractionalDiscount)
    assert applied_discount.factor == Decimal('0.5')


@pytest.mark.parametrize(
    'total, discount_value, discount_type, limit, expected_value', [
        ('100', 10, DiscountValueType.FIXED, None, 10),
        ('100.05', 10, DiscountValueType.PERCENTAGE, 100, 10)])
def test_value_voucher_checkout_discount(settings, total, discount_value,
                                         discount_type, limit, expected_value):
    voucher = Voucher(
        code='unique', type=VoucherType.VALUE,
        discount_value_type=discount_type,
        discount_value=discount_value,
        limit=Price(limit, currency='USD') if limit is not None else None)
    checkout = Mock(get_subtotal=Mock(return_value=Price(total,
                                                         currency='USD')))
    discount = voucher.get_discount_for_checkout(checkout)
    assert discount.amount == Price(expected_value, currency='USD')


def test_value_voucher_checkout_discount_not_applicable(settings):
    voucher = Voucher(
        code='unique', type=VoucherType.VALUE,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10,
        limit=100)
    checkout = Mock(get_subtotal=Mock(
        return_value=Price(10, currency='USD')))
    with pytest.raises(NotApplicable) as e:
        voucher.get_discount_for_checkout(checkout)
    assert e.value.limit == Price(100, currency='USD')


@pytest.mark.parametrize(
    'shipping_cost, shipping_country_code, discount_value, discount_type, apply_to, expected_value', [  # noqa
        (10, None, 50, DiscountValueType.PERCENTAGE, None, 5),
        (10, None, 20, DiscountValueType.FIXED, None, 10),
        (10, 'PL', 20, DiscountValueType.FIXED, '', 10),
        (5, 'PL', 5, DiscountValueType.FIXED, 'PL', 5)])
def test_shipping_voucher_checkout_discount(
        settings, shipping_cost, shipping_country_code, discount_value,
        discount_type, apply_to, expected_value):
    checkout = Mock(
        get_subtotal=Mock(return_value=Price(100, currency='USD')),
        is_shipping_required=True, shipping_method=Mock(
            price=Price(shipping_cost, currency='USD'),
            country_code=shipping_country_code))
    voucher = Voucher(
        code='unique', type=VoucherType.SHIPPING,
        discount_value_type=discount_type,
        discount_value=discount_value,
        apply_to=apply_to,
        limit=None)
    discount = voucher.get_discount_for_checkout(checkout)
    assert discount.amount == Price(expected_value, currency='USD')


@pytest.mark.parametrize(
    'is_shipping_required, shipping_method, discount_value, discount_type, '
    'apply_to, limit, subtotal, error_msg', [
        (True, Mock(country_code='PL'), 10, DiscountValueType.FIXED,
         'US', None, Price(10, currency='USD'),
         'This offer is only valid in United States of America.'),
        (True, None, 10, DiscountValueType.FIXED,
         None, None, Price(10, currency='USD'),
         'Please select a shipping method first.'),
        (False, None, 10, DiscountValueType.FIXED,
         None, None, Price(10, currency='USD'),
         'Your order does not require shipping.'),
        (True, Mock(price=Price(10, currency='USD')), 10,
         DiscountValueType.FIXED, None, 5, Price(2, currency='USD'),
         'This offer is only valid for orders over $5.00.')])
def test_shipping_voucher_checkout_discountnot_applicable(
        settings, is_shipping_required, shipping_method, discount_value,
        discount_type, apply_to, limit, subtotal, error_msg):
    checkout = Mock(is_shipping_required=is_shipping_required,
                    shipping_method=shipping_method,
                    get_subtotal=Mock(return_value=subtotal))
    voucher = Voucher(
        code='unique', type=VoucherType.SHIPPING,
        discount_value_type=discount_type,
        discount_value=discount_value,
        limit=Price(limit, currency='USD') if limit is not None else None,
        apply_to=apply_to)
    with pytest.raises(NotApplicable) as e:
        voucher.get_discount_for_checkout(checkout)
    assert str(e.value) == error_msg


def test_product_voucher_checkout_discount_not_applicable(settings,
                                                          monkeypatch):
    monkeypatch.setattr(
        'saleor.discount.models.get_product_variants_and_prices',
        lambda cart, product: [])
    voucher = Voucher(
        code='unique', type=VoucherType.PRODUCT,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10)
    checkout = Mock(cart=Mock())

    with pytest.raises(NotApplicable) as e:
        voucher.get_discount_for_checkout(checkout)
    assert str(e.value) == 'This offer is only valid for selected items.'


def test_category_voucher_checkout_discount_not_applicable(settings,
                                                           monkeypatch):
    monkeypatch.setattr(
        'saleor.discount.models.get_category_variants_and_prices',
        lambda cart, product: [])
    voucher = Voucher(
        code='unique', type=VoucherType.CATEGORY,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10)
    checkout = Mock(cart=Mock())
    with pytest.raises(NotApplicable) as e:
        voucher.get_discount_for_checkout(checkout)
    assert str(e.value) == 'This offer is only valid for selected items.'


def test_invalid_checkout_discount_form(monkeypatch, voucher):
    checkout = Mock(cart=Mock())
    form = CheckoutDiscountForm({'voucher': voucher.code}, checkout=checkout)
    monkeypatch.setattr(
        'saleor.discount.models.Voucher.get_discount_for_checkout',
        Mock(side_effect=NotApplicable('Not applicable')))
    assert not form.is_valid()
    assert 'voucher' in form.errors


def test_voucher_queryset_active(voucher):
    vouchers = Voucher.objects.all()
    assert len(vouchers) == 1
    active_vouchers = Voucher.objects.active(
        date=date.today() - timedelta(days=1))
    assert len(active_vouchers) == 0


def test_checkout_discount_form_active_queryset_voucher_not_active(voucher):
    assert len(Voucher.objects.all()) == 1
    checkout = Mock(cart=Mock())
    voucher.start_date = date.today() + timedelta(days=1)
    voucher.save()
    form = CheckoutDiscountForm({'voucher': voucher.code}, checkout=checkout)
    qs = form.fields['voucher'].queryset
    assert len(qs) == 0


def test_checkout_discount_form_active_queryset_voucher_active(voucher):
    assert len(Voucher.objects.all()) == 1
    checkout = Mock(cart=Mock())
    voucher.start_date = date.today()
    voucher.save()
    form = CheckoutDiscountForm({'voucher': voucher.code}, checkout=checkout)
    qs = form.fields['voucher'].queryset
    assert len(qs) == 1


def test_checkout_discount_form_active_queryset_after_some_time(voucher):
    assert len(Voucher.objects.all()) == 1
    checkout = Mock(cart=Mock())
    voucher.start_date = date(year=2016, month=6, day=1)
    voucher.end_date = date(year=2016, month=6, day=2)
    voucher.save()

    with freeze_time('2016-05-31'):
        form = CheckoutDiscountForm(
            {'voucher': voucher.code}, checkout=checkout)
        assert len(form.fields['voucher'].queryset) == 0

    with freeze_time('2016-06-01'):
        form = CheckoutDiscountForm(
            {'voucher': voucher.code}, checkout=checkout)
        assert len(form.fields['voucher'].queryset) == 1

    with freeze_time('2016-06-03'):
        form = CheckoutDiscountForm(
            {'voucher': voucher.code}, checkout=checkout)
        assert len(form.fields['voucher'].queryset) == 0


@pytest.mark.parametrize(
    'prices, discount_value, discount_type, apply_to, expected_value', [
        (
            [10], 10, DiscountValueType.FIXED,
            VoucherApplyToProduct.ONE_PRODUCT, 10),
        (
            [5], 10, DiscountValueType.FIXED,
            VoucherApplyToProduct.ONE_PRODUCT, 5),
        (
            [5, 5], 10, DiscountValueType.FIXED,
            VoucherApplyToProduct.ONE_PRODUCT, 10),
        (
            [2, 3], 10, DiscountValueType.FIXED,
            VoucherApplyToProduct.ONE_PRODUCT, 5),

        (
            [10, 10], 5, DiscountValueType.FIXED,
            VoucherApplyToProduct.ALL_PRODUCTS, 10),
        (
            [5, 2], 5, DiscountValueType.FIXED,
            VoucherApplyToProduct.ALL_PRODUCTS, 7),
        (
            [10, 10, 10], 5, DiscountValueType.FIXED,
            VoucherApplyToProduct.ALL_PRODUCTS, 15),

        ([10], 10, DiscountValueType.PERCENTAGE, None, 1),
        ([10, 10], 10, DiscountValueType.PERCENTAGE, None, 2)])
def test_products_voucher_checkout_discount_not(settings, monkeypatch, prices,
                                                discount_value, discount_type,
                                                apply_to, expected_value):
    monkeypatch.setattr(
        'saleor.discount.models.get_product_variants_and_prices',
        lambda cart, product: (
            (None, Price(p, currency='USD')) for p in prices))
    voucher = Voucher(
        code='unique', type=VoucherType.PRODUCT,
        discount_value_type=discount_type,
        discount_value=discount_value,
        apply_to=apply_to)
    checkout = Mock(cart=Mock())
    discount = voucher.get_discount_for_checkout(checkout)
    assert discount.amount == Price(expected_value, currency='USD')


@pytest.mark.django_db
def test_sale_applies_to_correct_products(product_type, default_category):
    product = Product.objects.create(
        name='Test Product', price=10, description='', pk=10,
        product_type=product_type, category=default_category)
    variant = ProductVariant.objects.create(product=product, sku='firstvar')
    product2 = Product.objects.create(
        name='Second product', price=15, description='',
        product_type=product_type, category=default_category)
    sec_variant = ProductVariant.objects.create(
        product=product2, sku='secvar', pk=10)
    sale = Sale.objects.create(
        name='Test sale', value=5, type=DiscountValueType.FIXED)
    sale.products.add(product)
    assert product2 not in sale.products.all()
    assert sale.modifier_for_product(variant.product).amount == Price(
        net=5, currency='USD')
    with pytest.raises(NotApplicable):
        sale.modifier_for_product(sec_variant.product)


def test_increase_voucher_usage():
    voucher = Voucher.objects.create(
        code='unique', type=VoucherType.VALUE,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10, usage_limit=100)
    increase_voucher_usage(voucher)
    voucher.refresh_from_db()
    assert voucher.used == 1


def test_decrease_voucher_usage():
    voucher = Voucher.objects.create(
        code='unique', type=VoucherType.VALUE,
        discount_value_type=VoucherType.VALUE,
        discount_value=10, usage_limit=100, used=10)
    decrease_voucher_usage(voucher)
    voucher.refresh_from_db()
    assert voucher.used == 9


def _test_discount(client):
    """Test if discount is correctly applied in frontstore."""

    def _assert_product_details_view(product, expected_price):
        """Test product details view, it looks at the variant picker JSON data."""
        test_url = product.get_absolute_url()
        response = client.get(test_url)
        assert response.status_code == 200
        data = json_variant_details(response.content)
        assert data['variants'][0]['price']['net'] == str(expected_price)

    def _wrapper(product: Product, expected_discount):
        expected_price = product.price.net - expected_discount
        _assert_product_details_view(product, expected_price)

    return _wrapper


def _test_discount_on_customers(client: Client, test_suite):
    """Test if discount is correctly applied to specific customers in frontstore.
    User must be None to be Anonymous.
    """
    def _wrapper(product, *user_vs_expected):
        for user, expected in user_vs_expected:
            client.logout()
            if user:
                client.login(username=user.email, password='password')

            test_suite(product, expected)

    return _wrapper


def test_customer_sale_all_store(
        client: Client, staff_user,
        customer_user: User, product_in_stock: Product):

    test_discount = _test_discount(client)
    test_on_customers = _test_discount_on_customers(client, test_discount)
    client.login(username=customer_user.email, password='password')

    sale = Sale.objects.create(name='Test sale', value=Decimal(2.0))

    # No discount should be applied
    test_discount(product_in_stock, Decimal(0.0))

    sale.customers.add(customer_user)
    sale.save()

    # Test whether discount is applied or not on customer, staff user and anonymous user.
    test_on_customers(
        product_in_stock,

        # -- Only this customer should get the discount
        (customer_user, Decimal(2.0)),

        # -- Anonymous user shouldn't have any discount
        (None, Decimal(0.0)),

        # -- Staff user shouldn't have any discount since it's a different customer
        (staff_user, Decimal(0.0)),
    )


def test_customer_sale_specific_product(
        client: Client, staff_user,
        customer_user: User, variant_list, stock_location: StockLocation):

    products = []
    for variant in variant_list:  # type: ProductVariant
        Stock.objects.create(
            variant=variant, cost_price=10, quantity=5, location=stock_location)
        variant.product.is_published = True
        variant.product.save()
        products.append(variant.product)

    discounted_product = products[0]
    non_discounted_product = products[1]

    test_discount = _test_discount(client)
    test_on_customers = _test_discount_on_customers(client, test_discount)
    client.login(username=customer_user.email, password='password')

    sale = Sale.objects.create(name='Test sale', value=Decimal(2.0))

    # No discount should be applied
    test_discount(discounted_product, Decimal(0.0))
    test_discount(non_discounted_product, Decimal(0.0))

    sale.customers.add(customer_user)
    sale.products.add(discounted_product)
    sale.save()

    # Test whether discount is applied or not on customer, staff user and anonymous user.
    test_on_customers(
        discounted_product,

        # -- Only this customer should get the discount
        (customer_user, Decimal(2.0)),

        # -- Anonymous user shouldn't have any discount
        (None, Decimal(0.0)),

        # -- Staff user shouldn't have any discount since it's a different customer
        (staff_user, Decimal(0.0)),
    )

    # Test whether discount is not applied when the product is not targeted
    test_on_customers(
        non_discounted_product,

        # -- The customer shouldn't get the discount
        (customer_user, Decimal(0.0)),

        # -- Anonymous user shouldn't have any discount
        (None, Decimal(0.0)),

        # -- Staff user shouldn't have any discount since it's a different customer
        (staff_user, Decimal(0.0)),
    )


def test_customer_sale_specific_category(
        client: Client, staff_user,
        customer_user: User, variant_list, stock_location: StockLocation):

    NO_DISCOUNT_FOR_ALMOST_EVERYONE = (
        # -- Anonymous user shouldn't have any discount
        (None, Decimal(0.0)),

        # -- Staff user shouldn't have any discount since it's a different customer
        (staff_user, Decimal(0.0)))

    NO_DISCOUNT_FOR_EVERYONE = (
        # -- This customer shouldn't get the discount
        (customer_user, Decimal(0.0)), *NO_DISCOUNT_FOR_ALMOST_EVERYONE)

    DISCOUNT_ONLY_FOR_CUSTOMER_1 = ((customer_user, Decimal(2.0)), *NO_DISCOUNT_FOR_ALMOST_EVERYONE)

    products = []
    for variant in variant_list:  # type: ProductVariant
        Stock.objects.create(
            variant=variant, cost_price=10, quantity=5, location=stock_location)
        variant.product.is_published = True
        variant.product.save()
        products.append(variant.product)

    discounted_product = products[0]
    discounted_product2 = products[1]

    test_discount = _test_discount(client)
    test_on_customers = _test_discount_on_customers(client, test_discount)
    client.login(username=customer_user.email, password='password')

    sale = Sale.objects.create(name='Test sale', value=Decimal(2.0))

    # No discount should be applied
    test_discount(discounted_product, Decimal(0.0))
    test_discount(discounted_product2, Decimal(0.0))

    sale.customers.add(customer_user)
    sale.categories.add(discounted_product.category)
    sale.save()

    # Test whether discount is applied or not on customer, staff user and anonymous user.
    test_on_customers(
        discounted_product,

        # -- Only this customer should get the discount
        *DISCOUNT_ONLY_FOR_CUSTOMER_1
    )

    # Test whether discount is not applied when the product is not targeted
    test_on_customers(
        discounted_product2,

        # -- Only this customer should get the discount
        *DISCOUNT_ONLY_FOR_CUSTOMER_1
    )

    # Test whether discount is or is not applied when the product category is not targeted
    discounted_product2.category = Category.objects.create(name='New category', slug='new-cat')
    discounted_product2.save()
    test_on_customers(
        discounted_product2,

        # -- Nobody should get the discount on this category
        *NO_DISCOUNT_FOR_EVERYONE
    )

    # Test whether discount is or is not applied when the product category is not targeted but the product is targeted
    sale.products.add(discounted_product2)
    sale.save()
    test_on_customers(
        discounted_product2,

        # -- Only the first customer should get the discount on this category
        *DISCOUNT_ONLY_FOR_CUSTOMER_1
    )
