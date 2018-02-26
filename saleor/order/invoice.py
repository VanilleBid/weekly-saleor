import os.path

from django.conf import settings

from invoice_generator import models
from invoice_generator import builder

PDF_STATIC_PATH = os.path.join(settings.REAL_STATIC_ROOT, 'invoice')


def _generate_pdf_billing_address(order):
    billing_address = order.billing_address

    billing_address = models.Address(
        name=billing_address.full_name,
        street=billing_address.street_address_1,
        postcode=billing_address.postal_code,
        city=billing_address.country.name)

    return billing_address


def _generate_pdf_data(order):
    order_total = order.total
    order_data = dict(
        date=order.created,
        tax_rate=order.tax_rate,
        payment_date_limit=None,
        shipping_date_range=None,
        total_discounted=None,
        total_tax=order.total_tax.net,
        total_shipping_net=order.shipping_price.net,
        total_net=order_total.net, total_gross=order_total.gross)

    if order.is_shipping_required():
        order_data['shipping_date_range'] = (
            order.shipping_date, order.max_shipping_date)

    if order.discount_amount:
        order_data['total_discounted'] = order.discount_amount.net

    order_obj = models.Order(order.id, order.user_id, **order_data)

    return order_obj


def _generate_pdf_items(order, order_data):
    items = []

    for item in order.get_lines():
        items.append(
            models.OrderItem(
                order_data, item.id, item.product_name,
                item.quantity, item.unit_price_net, item.get_total().net))

    return items


def _generate_pdf_invoice(order_data, billing_address, items):
    invoice = models.Invoice(
        order_data, settings.INVOICE_VENDOR, billing_address, items)

    return invoice


def create_invoice(order):
    order_data = _generate_pdf_data(order)
    billing_address = _generate_pdf_billing_address(order)
    items = _generate_pdf_items(order, order_data)
    invoice = _generate_pdf_invoice(order_data, billing_address, items)

    return invoice


def create_invoice_html(order):
    invoice = create_invoice(order)
    html = builder.generate_html(settings.DEFAULT_CURRENCY, invoice, None)
    return html


def create_invoice_pdf(order):
    html = create_invoice_html(order)
    pdf = builder.generate_pdf_from(html, static_path=PDF_STATIC_PATH)
    return pdf
