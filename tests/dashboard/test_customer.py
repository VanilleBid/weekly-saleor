from saleor.userprofile.models import User
from saleor.dashboard.customer.forms import CustomerForm


def test_customer_form():
    data = {'email': 'newcustomer@example.com', 'is_active': True}
    form = CustomerForm(data)
    assert form.is_valid()
    form.save()
    assert User.objects.get(email=data['email'])
