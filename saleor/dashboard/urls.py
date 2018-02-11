from django.conf.urls import include, url

from saleor.dashboard.views import send_test_mail
from . import views as core_views
from .category.urls import urlpatterns as category_urls
from .collection.urls import urlpatterns as collection_urls
from .customer.urls import urlpatterns as customer_urls
from .discount.urls import urlpatterns as discount_urls
from .group.urls import urlpatterns as groups_urls
from .order.urls import urlpatterns as order_urls
from .product.urls import urlpatterns as product_urls
from .search.urls import urlpatterns as search_urls
from .shipping.urls import urlpatterns as shipping_urls
from .sites.urls import urlpatterns as site_urls
from .staff.urls import urlpatterns as staff_urls

urlpatterns = [
    url(r'^$', core_views.index, name='index'),
    url(r'^categories/', include(category_urls)),
    url(r'^collections/', include(collection_urls)),
    url(r'^orders/', include(order_urls)),
    url(r'^products/', include(product_urls)),
    url(r'^customers/', include(customer_urls)),
    url(r'^staff/', include(staff_urls)),
    url(r'^groups/', include(groups_urls)),
    url(r'^discounts/', include(discount_urls)),
    url(r'^settings/', include(site_urls)),
    url(r'^shipping/', include(shipping_urls)),
    url(r'^style-guide/', core_views.styleguide, name='styleguide'),
    url(r'^search/', include(search_urls)),
    url(r'^test-mail/', send_test_mail)
]
