# -- patch #125
# ---- Custom legal bottom text for both, frontstore and emails
# -- https://github.com/VanilleBid/weekly-saleor/issues/125

from unittest import mock
from pytest import fixture
from django.test import Client

from saleor.order import emails
from saleor.site.models import SiteSettings


FOOTER_TEXT = 'Hello, this is the bottom.'


@fixture()
def site_settings_with_footer(site_settings: SiteSettings):
    site_settings.footer_text = FOOTER_TEXT
    site_settings.save()
    return site_settings


def test_home_with_footer(site_settings_with_footer):
    resp = Client().get('/')
    assert resp.status_code == 200
    assert resp.content.find(FOOTER_TEXT.encode('utf-8')) > 0


@mock.patch('saleor.order.emails.send_templated_mail')
def test_order_mail_with_footer(mocked_tpl, site_settings_with_footer, order):
    emails.send_order_confirmation('customer@example.com', 'hello', order.pk)

    calls = mocked_tpl.mock_calls
    assert len(calls) == 1

    name, args, kwargs = calls[0]
    footer_text = kwargs['context'].get('footer_text', None)
    assert footer_text
    assert footer_text == FOOTER_TEXT


def test_home_without_footer(site_settings):
    resp = Client().get('/')
    assert resp.status_code == 200
    assert resp.content.find(FOOTER_TEXT.encode('utf-8')) == -1


@mock.patch('saleor.order.emails.send_templated_mail')
def test_order_mail_without_footer(mocked_tpl, site_settings, order):
    emails.send_order_confirmation('customer@example.com', 'hello', order.pk)

    calls = mocked_tpl.mock_calls
    assert len(calls) == 1

    name, args, kwargs = calls[0]
    footer_text = kwargs['context'].get('footer_text', None)
    assert footer_text == ''
