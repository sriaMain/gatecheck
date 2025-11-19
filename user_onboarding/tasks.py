


from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

@shared_task
def send_credentials_email(email, user_id, raw_password, username):
    subject = "SmartCheck Login Credentials"
    from_email = settings.EMAIL_HOST_USER
    to = [email]

    context = {
        "username": username,
        "user_id": user_id,
        "password": raw_password,
        "login_url": "http://yourapp.com/login/"
    }

    html_content = render_to_string("emails/login.html", context)

    email_msg = EmailMultiAlternatives(subject, "", from_email, to)
    email_msg.attach_alternative(html_content, "text/html")
    email_msg.send()


