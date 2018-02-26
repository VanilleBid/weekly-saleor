from django.conf import settings
from django.contrib.admin.views.decorators import (
    staff_member_required as _staff_member_required, user_passes_test)
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.mail import send_mail
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponseBadRequest
from django.template.response import TemplateResponse
from payments import PaymentStatus

from ..order.models import Order, Payment
from ..product.models import Product


def staff_member_required(f):
    return _staff_member_required(f, login_url='account_login')


def superuser_required(
        view_func=None, redirect_field_name=REDIRECT_FIELD_NAME,
        login_url='account_login'):
    """Check if the user is logged in and is a superuser.

    Otherwise redirects to the login page.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name)
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


@staff_member_required
def index(request):
    paginate_by = 10
    orders_to_ship = Order.objects.open().select_related(
        'user').prefetch_related('groups', 'groups__lines', 'payments')
    orders_to_ship = [
        order for order in orders_to_ship if order.is_fully_paid()]
    payments = Payment.objects.filter(
        status=PaymentStatus.PREAUTH).order_by('-created')
    payments = payments.select_related('order', 'order__user')
    low_stock = get_low_stock_products()
    ctx = {'preauthorized_payments': payments[:paginate_by],
           'orders_to_ship': orders_to_ship[:paginate_by],
           'low_stock': low_stock[:paginate_by]}
    return TemplateResponse(request, 'dashboard/index.html', ctx)


@staff_member_required
def styleguide(request):
    return TemplateResponse(request, 'dashboard/styleguide/index.html', {})


def get_low_stock_products():
    threshold = getattr(settings, 'LOW_STOCK_THRESHOLD', 10)
    products = Product.objects.annotate(
        total_stock=Sum('variants__stock__quantity'))
    return products.filter(Q(total_stock__lte=threshold)).distinct()


@staff_member_required
def send_test_mail(request):
    if 'recipient' not in request.GET:
        return HttpResponseBadRequest()

    data = {
        'subject': 'Dummy message',
        'message': 'Here is the message...',
        'from_email': settings.EMAIL_HOST_USER,
        'recipient_list': request.GET.getlist('recipient'),
        'fail_silently': False
    }

    return JsonResponse({
        'EMAIL_USE_TLS': settings.EMAIL_USE_TLS,
        'EMAIL_BACKEND': settings.EMAIL_BACKEND,
        'EMAIL_HOST': settings.EMAIL_HOST,
        'EMAIL_HOST_PASSWORD': settings.EMAIL_HOST_PASSWORD,
        'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
        'EMAIL_PORT': settings.EMAIL_PORT,
        'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
        'results': {
            'sent': send_mail(**data),
            **data
        }
    })
