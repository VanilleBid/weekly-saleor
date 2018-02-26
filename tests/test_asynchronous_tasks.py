import pytest

from unittest.mock import MagicMock

from django_webhooking.ext.DummyWebhook import DummyAdapter
from prices import Price

from saleor.order.emails import (
    send_order_confirmation, send_payment_confirmation)
from saleor.order.models import Order, OrderNote
from saleor.userprofile.models import User


@pytest.mark.django_db
@pytest.mark.integration
def test_email_sending_asynchronously(
        transactional_db, celery_app, celery_worker, order_with_lines):
    order = send_order_confirmation.delay(
        'joe.doe@foo.com', '/nowhere/to/go', order_with_lines.pk)
    payment = send_payment_confirmation.delay('joe.doe@foo.com', '/nowhere/')
    order.get()
    payment.get()


def test_webhooks(billing_address, customer_user, order: Order):
    mocked = DummyAdapter.send = MagicMock(wraps=DummyAdapter.send)

    to_hook = (
        Order(billing_address=billing_address, user=customer_user,
              user_email=customer_user.email,
              total=Price(123, currency='USD')),

        User(email='test@example.org', password='test'),

        OrderNote(order=order, user=customer_user),
    )

    for hook in to_hook:
        mocked.reset_mock()
        hook.save()
        embed = hook.webhook_embed(True).to_dict()
        DummyAdapter.send.assert_called_once_with(embed=embed)
