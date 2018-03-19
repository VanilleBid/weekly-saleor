from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^permalink/$', views.get_cart_permalink, name='get-cart-permalink'),
    url(r'^get/(?P<variant_quantity>(\d{1,10}-\d{1,2}-)*(\d{1,10}-\d{1,2}))/', views.get_cart, name='get-cart'),
    url(r'^update/(?P<variant_id>\d+)/$', views.update, name='update-line'),
    url(r'^summary/$', views.summary, name='cart-summary'),
    url(r'^shipingoptions/$', views.get_shipping_options,
        name='shipping-options')]
