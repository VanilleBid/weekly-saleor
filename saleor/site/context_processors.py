from django.contrib.sites.shortcuts import get_current_site
from django.utils.functional import cached_property


class SocialLinks:
    @cached_property
    def facebook(self):
        from django.conf import settings
        return settings.SOCIAL_LINKS_FACEBOOK

    @cached_property
    def twitter(self):
        from django.conf import settings
        return settings.SOCIAL_LINKS_TWITTER

    @cached_property
    def instagram(self):
        from django.conf import settings
        return settings.SOCIAL_LINKS_INSTAGRAM


def site(request):
    # type: (django.http.request.HttpRequest) -> dict
    """Add site settings to the context under the 'site' key."""
    return {'site': get_current_site(request), 'social_links': SocialLinks}
