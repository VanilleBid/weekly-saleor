import uuid
from ...checkout.core import Checkout
from ...discount.models import Voucher


class FakeCheckout(Checkout):
    def __init__(self, voucher: Voucher, *args, **kwargs):
        super(FakeCheckout, self).__init__(*args, **kwargs)
        self._given_voucher = voucher
        if voucher:
            self.voucher_code = 'code'
            self.recalculate_discount()

    def _get_voucher(self, vouchers=None):
        return self._given_voucher


class FakeVoucher(Voucher):
    class Meta:
        proxy = True

    def __init__(self, *args, **kwargs):
        super(FakeVoucher, self).__init__(*args, **kwargs)
        code_max_length = self.__class__._meta.get_field('code').max_length
        self.code = str(uuid.uuid4())[:code_max_length]

    def get_discount_for_checkout(self, checkout):
        cart_total = checkout.get_subtotal()
        return self.get_fixed_discount_for(cart_total)
