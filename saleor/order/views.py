import logging

from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponseForbidden, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy
from payments import PaymentStatus, RedirectNeeded

from . import OrderStatus
from ..core.utils import get_client_ip
from ..registration.forms import LoginForm
from ..userprofile.models import User
from .forms import (
    OrderNoteForm, PasswordForm, PaymentDeleteForm, PaymentMethodsForm)
from .models import Order, OrderNote, Payment
from .utils import attach_order_to_user, check_order_status
from .invoice import create_invoice_pdf

logger = logging.getLogger(__name__)


def user_is_staff_or_can(user, permission_name):
    is_staff = user.is_active and user.is_staff
    staff_and_perm = is_staff and user.has_perms((permission_name, ))
    return staff_and_perm


def _can_view_pdf_invoice(view):
    def _wrapper(request, token):
        order = get_object_or_404(Order.objects, token=token)
        if order.user == request.user or \
                user_is_staff_or_can(request.user, 'order.view_order'):
            return view(request, order)
        raise Http404
    return _wrapper


def details(request, token):
    orders = Order.objects.prefetch_related('groups__lines__product')
    orders = orders.select_related(
        'billing_address', 'shipping_address', 'user')
    order = get_object_or_404(orders, token=token)
    groups = order.groups.all()
    notes = order.notes.filter(is_public=True)
    ctx = {'order': order, 'groups': groups, 'notes': notes}
    if order.status == OrderStatus.OPEN:
        user = request.user if request.user.is_authenticated else None
        note = OrderNote(order=order, user=user)
        note_form = OrderNoteForm(request.POST or None, instance=note)
        ctx.update({'note_form': note_form})
        if request.method == 'POST':
            if note_form.is_valid():
                note_form.save()
                return redirect('order:details', token=order.token)
    return TemplateResponse(request, 'order/details.html', ctx)


@login_required
@_can_view_pdf_invoice
def invoice(request, order):
    pdf = create_invoice_pdf(order).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    name = "invoice-%s" % order.id
    response['Content-Disposition'] = 'filename=%s' % name
    return response


def payment(request, token):
    orders = Order.objects.prefetch_related('groups__lines__product')
    orders = orders.select_related(
        'billing_address', 'shipping_address', 'user')
    order = get_object_or_404(orders, token=token)
    groups = order.groups.all()
    payments = order.payments.all()
    form_data = request.POST or None
    try:
        waiting_payment = order.payments.get(status=PaymentStatus.WAITING)
    except Payment.DoesNotExist:
        waiting_payment = None
        waiting_payment_form = None
    else:
        form_data = None
        waiting_payment_form = PaymentDeleteForm(
            None, order=order, initial={'payment_id': waiting_payment.id})
    if order.is_fully_paid():
        form_data = None
    payment_form = None
    if not order.is_pre_authorized():
        payment_form = PaymentMethodsForm(form_data)
        # FIXME: redirect if there is only one payment method
        if payment_form.is_valid():
            payment_method = payment_form.cleaned_data['method']
            return redirect(
                'order:payment', token=order.token, variant=payment_method)
    ctx = {
        'order': order, 'groups': groups, 'payment_form': payment_form,
        'payments': payments, 'waiting_payment': waiting_payment,
        'waiting_payment_form': waiting_payment_form}
    return TemplateResponse(request, 'order/payment.html', ctx)


@check_order_status
def start_payment(request, order, variant):
    waiting_payments = order.payments.filter(
        status=PaymentStatus.WAITING).exists()
    if waiting_payments:
        return redirect('order:payment', token=order.token)
    billing = order.billing_address
    total = order.get_total()
    defaults = {
        'total': total.gross,
        'tax': total.tax, 'currency': total.currency,
        'delivery': order.shipping_price.gross,
        'billing_first_name': billing.first_name,
        'billing_last_name': billing.last_name,
        'billing_address_1': billing.street_address_1,
        'billing_address_2': billing.street_address_2,
        'billing_city': billing.city,
        'billing_postcode': billing.postal_code,
        'billing_country_code': billing.country.code,
        'billing_email': order.user_email,
        'description': pgettext_lazy(
            'Payment description', 'Order %(order_number)s') % {
                'order_number': order},
        'billing_country_area': billing.country_area,
        'customer_ip_address': get_client_ip(request)}
    variant_choices = settings.CHECKOUT_PAYMENT_CHOICES
    if variant not in [code for code, dummy_name in variant_choices]:
        raise Http404('%r is not a valid payment variant' % (variant,))
    with transaction.atomic():
        payment, dummy_created = Payment.objects.get_or_create(
            variant=variant, status=PaymentStatus.WAITING, order=order,
            defaults=defaults)
        try:
            form = payment.get_form(data=request.POST or None)
        except RedirectNeeded as redirect_to:
            return redirect(str(redirect_to))
        except Exception:
            logger.exception('Error communicating with the payment gateway')
            msg = pgettext_lazy(
                'Payment gateway error',
                'Oops, it looks like we were unable to contact the selected '
                'payment service')
            messages.error(request, msg)
            payment.change_status(PaymentStatus.ERROR)
            return redirect('order:payment', token=order.token)
    template = 'order/payment/%s.html' % variant
    ctx = {'form': form, 'payment': payment}
    return TemplateResponse(
        request, [template, 'order/payment/default.html'], ctx)


@check_order_status
def cancel_payment(request, order):
    form = PaymentDeleteForm(request.POST or None, order=order)
    if form.is_valid():
        with transaction.atomic():
            form.save()
        return redirect('order:payment', token=order.token)
    return HttpResponseForbidden()


def checkout_success(request, token):
    """Redirect user after placing an order.

    Anonymous users are redirected to the checkout success page.
    Registered users are redirected to order details page and the order
    is attached to their account.
    """
    order = get_object_or_404(Order, token=token)
    email = order.user_email
    ctx = {'email': email, 'order': order}
    if request.user.is_authenticated:
        return TemplateResponse(request, 'order/checkout_success.html', ctx)
    form_data = request.POST.copy()
    if form_data:
        form_data.update({'email': email})
    register_form = PasswordForm(form_data or None)
    if register_form.is_valid():
        register_form.save()
        password = register_form.cleaned_data.get('password')
        user = auth.authenticate(
            request=request, email=email, password=password)
        auth.login(request, user)
        attach_order_to_user(order, user)
        return redirect('order:details', token=token)
    user_exists = User.objects.filter(email=email).exists()
    login_form = LoginForm(
        initial={'username': email}) if user_exists else None
    ctx.update({'form': register_form, 'login_form': login_form})
    return TemplateResponse(
        request, 'order/checkout_success_anonymous.html', ctx)


@login_required
def connect_order_with_user(request, token):
    """Connect newly created order to an authenticated user."""
    try:
        order = Order.objects.get(user_email=request.user.email, token=token)
    except Order.DoesNotExist:
        order = None
    if not order:
        msg = pgettext_lazy(
            'Connect order with user warning message',
            "We couldn't assign the order to your account as the email"
            " addresses don't match")
        messages.warning(request, msg)
        return redirect('profile:details')
    attach_order_to_user(order, request.user)
    msg = pgettext_lazy(
        'storefront message',
        'The order is now assigned to your account')
    messages.success(request, msg)
    return redirect('order:details', token=order.token)
