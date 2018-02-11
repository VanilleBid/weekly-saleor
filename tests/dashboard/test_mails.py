import json

from unittest import mock

from django.conf import settings
from django.test import Client


@mock.patch('django.core.mail.send_mail')
def test_staff_form_not_valid(mocked_send_mail, client: Client, admin_client: Client):
    endpoint = '/dashboard/test-mail/'
    recipients = ['a@example.org', 'b@example.org']

    request = client.get(endpoint)
    assert request.status_code == 302

    request = admin_client.get(endpoint)
    assert request.status_code == 400

    request = admin_client.get(endpoint, {'recipient': recipients})

    assert request.status_code == 200
    assert json.loads(
        request.content.decode('utf-8')
    ) == {
        'EMAIL_USE_TLS': False,
        'EMAIL_BACKEND': 'django.core.mail.backends.locmem.EmailBackend',
        'EMAIL_HOST': None,
        'EMAIL_HOST_PASSWORD': None,
        'EMAIL_HOST_USER': None,
        'EMAIL_PORT': None,
        'DEFAULT_FROM_EMAIL': None,
        'results': {
            'subject': 'Dummy message',
            'message': 'Here is the message...',
            'from_email': None,
            'recipient_list': recipients,
            'fail_silently': False
        }
    }

    mocked_send_mail.assert_called_once_with(
        subject='Dummy message',
        message='Here is the message...',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=recipients,
        fail_silently=False
    )
