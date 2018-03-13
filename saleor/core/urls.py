from django.conf.urls import url
from django.template.response import TemplateResponse
from impersonate.views import stop_impersonate

from . import views


def static_page(
        endpoint, name=None, prefix=None,
        template_extension=None, content_type=None):

    name = name or endpoint.strip('/')
    template = r'%s%s' % (
        name.replace('-', '_'),
        template_extension is None and '.html' or template_extension)

    def _view(request):
        return TemplateResponse(
            request, template, content_type=content_type)

    return url(
        r'^%s%s$' % (
            prefix is None and 'pages/' or prefix, endpoint
        ), _view, name=name
    )


urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^style-guide/', views.styleguide, name='styleguide'),
    url(r'^impersonate/(?P<uid>\d+)/', views.impersonate,
        name='impersonate-start'),
    url(r'^impersonate/stop/$', stop_impersonate,
        name='impersonate-stop'),
    url(r'^404', views.handle_404, name='handle-404'),
    url(r'^manifest\.json$', views.manifest, name='manifest'),
    static_page(
        'robots.txt',
        prefix='', template_extension='', content_type='text/plain'),
]
