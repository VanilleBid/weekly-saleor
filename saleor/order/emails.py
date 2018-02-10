from celery import shared_task
from django.conf import settings
from django.contrib.sites.models import Site
from templated_email import send_templated_mail

CONFIRM_ORDER_TEMPLATE = 'order/confirm_order'
CONFIRM_PAYMENT_TEMPLATE = 'order/payment/confirm_payment'
CONFIRM_NOTE_TEMPLATE = 'order/note/confirm_note'
CONFIRM_SHIPPING_TEMPLATE = 'order/confirm_shipping'


def _send_confirmation(email, url, template, **ctx_kwargs):
    site = Site.objects.get_current()
    send_templated_mail(
        from_email=settings.ORDER_FROM_EMAIL,
        recipient_list=[email],
        context=dict(site_name=site.name, url=url, **ctx_kwargs),
        template_name=template)


@shared_task
def send_order_confirmation(email, url):
    _send_confirmation(email, url, CONFIRM_ORDER_TEMPLATE)


@shared_task
def send_payment_confirmation(email, url):
    _send_confirmation(email, url, CONFIRM_PAYMENT_TEMPLATE)


@shared_task
def send_note_confirmation(email, url):
    _send_confirmation(email, url, CONFIRM_NOTE_TEMPLATE)


@shared_task
def send_shipping_confirmation(email, url, tracking_url):
    _send_confirmation(email, url, CONFIRM_SHIPPING_TEMPLATE, tracking_url=tracking_url)
