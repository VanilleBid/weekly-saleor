from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^media/$', views.media_bucket, name='bucket-media'),
    url(r'^static/$', views.static_bucket, name='bucket-static')]
