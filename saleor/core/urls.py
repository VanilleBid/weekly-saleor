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
]

if settings.DEBUG:
    def robots(request):
        return HttpResponse(b'User-agent: *\nDisallow: /', content_type='text/plain')
    urlpatterns.append(url(r'^robots\.txt$', robots, name='robots'))
