import templated_email
from django.conf import settings


def send_templated_mail(
        template_name, from_email, recipient_list, context,
        *args, **kwargs):

    return templated_email.send_templated_mail(
        template_name, from_email, recipient_list, context,
        *args, **kwargs)
