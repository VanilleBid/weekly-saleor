import json
from django.test import Client


def test_staff_form_not_valid(client: Client, admin_client: Client):
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
            'sent': 1,
            'subject': 'Dummy message',
            'message': 'Here is the message...',
            'from_email': None,
            'recipient_list': recipients,
            'fail_silently': False
        }
    }
