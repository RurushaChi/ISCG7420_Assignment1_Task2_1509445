# booking/utils.py

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

def send_booking_email(user_email, subject, template_name, context):
    """
    Sends an email using a template (HTML + text) for booking notifications.
    `template_name` is base name (without extension), so you must have
       templates/emails/<template_name>.html
       templates/emails/<template_name>.txt
    `context` is a dict you pass to render templates.
    """
    # Render text and html versions
    text_body = render_to_string(f"emails/{template_name}.txt", context)
    html_body = render_to_string(f"emails/{template_name}.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user_email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send()
