from django.conf.urls import url
from django.http import HttpResponse
from impersonate.views import stop_impersonate

from saleor import settings
from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^style-guide/', views.styleguide, name='styleguide'),
    url(r'^impersonate/(?P<uid>\d+)/', views.impersonate,
        name='impersonate-start'),
    url(r'^impersonate/stop/$', stop_impersonate,
        name='impersonate-stop'),
    url(r'^404', views.handle_404, name='handle-404'),
    url(r'^manifest\.json$', views.manifest, name='manifest'),
    url(r'^pages/privacy/$', views.privacy_policy, name='privacy-policy'),
    url(r'^pages/contract/$', views.selling_contract, name='selling-contract')
]

if settings.DEBUG:
    ROBOTS_TXT = b'User-agent: *\nDisallow: /'

    def robots(request):
        return HttpResponse(ROBOTS_TXT, content_type='text/plain')
    urlpatterns.append(url(r'^robots\.txt$', robots, name='robots'))
