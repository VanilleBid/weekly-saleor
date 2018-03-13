import templated_email
from django.conf import settings


def get_context():
    return {
        'footer_text': settings.EMAIL_FOOTER_TEXT
    }


def send_templated_mail(
        template_name, from_email, recipient_list, context,
        *args, **kwargs):

    context.update(get_context())

    return templated_email.send_templated_mail(
        template_name, from_email, recipient_list, context,
        *args, **kwargs)
