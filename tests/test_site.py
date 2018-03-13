from django.test import Client
from django.urls import reverse
from django.conf import settings

from saleor.site.context_processors import SocialLinks


def test_home_social_links(client: Client):
    def _get_social_expected_url(_prop_name):
        _prop_expected_value = getattr(settings, 'SOCIAL_LINKS_' + _prop_name.upper())
        return '{}.com/{}'.format(_prop_name, _prop_expected_value)

    url = reverse('home')
    social_sites = [
        prop for prop in SocialLinks.__dict__.keys() if not prop.startswith('_')
    ]

    expected_lines = [
        _get_social_expected_url(site) for site in social_sites
    ]

    response = client.get(url)
    assert response.status_code == 200

    footer_start = response.content.find(b'<footer ')
    assert footer_start > 0

    footer_content = response.content[footer_start:].decode('utf-8')
    for line in expected_lines:
        assert line in footer_content
