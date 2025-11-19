from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Visitor
import django_filters
from django.db.models import Q
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import uuid
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_email_task(self, subject, message, recipient_list, html_message=None):
    """Generic email sending task with retry logic"""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"Email sent successfully to {recipient_list}")
        return f"Email sent successfully to {recipient_list}"
    except Exception as exc:
        logger.error(f"Failed to send email to {recipient_list}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)

logger = logging.getLogger(__name__)





@shared_task
def send_visit_scheduled_email(visitor_id, entry_otp, exit_otp):
    try:
        visitor = Visitor.objects.get(id=visitor_id)

        subject = "Visit Scheduled"

        company_name = visitor.coming_from.strip().title() if visitor.coming_from else "our facility"

        message = (
            f"Dear {visitor.visitor_name},\n\n"
            f"Your visit is scheduled at {company_name} on {visitor.visiting_date.strftime('%d-%m-%Y')}.\n\n"
            f"Entry OTP: {entry_otp}\n"
            f"Exit OTP: {exit_otp}\n"
            f"Visitor Pass Number: {visitor.pass_id}\n"
        )

        send_mail(subject, message, "no-reply@example.com", [visitor.email_id])
    
    except Visitor.DoesNotExist:
        print(f"Visitor with ID {visitor_id} does not exist.")
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise
        
    



@shared_task
def send_checkin_confirmation_email(visitor_id, visitor_pass_number):
    """Send check-in confirmation email with ePass link"""
    try:
        visitor = Visitor.objects.get(id=visitor_id)
        
        subject = "Successfully Checked-in - Your ePass is Ready"
        
        # Generate ePass URL (similar to the hub.ismartcheck.com URLs in SMS)
        epass_url = f"{settings.EPASS_BASE_URL}/epass/{visitor.unique_code}"
        
        context = {
            'visitor_name': visitor.name,
            'company_name': visitor.company_name,
            'visitor_pass_number': visitor_pass_number,
            'epass_url': epass_url,
            'checkin_time': timezone.now().strftime('%d-%m-%Y %I:%M %p'),
        }
        
        # HTML email template
        html_message = render_to_string('emails/checkin_confirmation.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[visitor.email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Check-in confirmation email sent to {visitor.email}")
        return f"Check-in confirmation email sent to {visitor.email}"
        
    except Visitor.DoesNotExist:
        logger.error(f"Visitor with ID {visitor_id} not found")
        return f"Visitor with ID {visitor_id} not found"
    except Exception as exc:
        logger.error(f"Failed to send check-in confirmation email: {str(exc)}")
        raise exc

@shared_task
def cleanup_expired_visitors():
    """Mark expired visitors as expired"""
    try:
        expired_visitors = Visitor.objects.filter(
            valid_until__lt=timezone.now(),
            status=Visitor.PassStatus.APPROVED
        )
        count = expired_visitors.update(status=Visitor.PassStatus.EXPIRED)
        logger.info(f"Marked {count} visitors as expired")
        return f"Marked {count} visitors as expired"
    except Exception as exc:
        logger.error(f"Failed to cleanup expired visitors: {str(exc)}")
        raise exc




from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import Visitor


@shared_task
def send_visitor_approval_email(visitor_id):
    try:
        visitor = Visitor.objects.get(id=visitor_id)
        host = visitor.host_employee

        # These links should point to your site endpoint that handles approval via browser
        approve_url = f"{settings.BASE_URL}/visitor/decision/{visitor.id}/?action=approve"
        reject_url = f"{settings.BASE_URL}/visitor/decision/{visitor.id}/?action=reject"

        context = {
            "host_name": host.get_full_name() if host else "",
            "visitor_name": visitor.visitor_name,
            "company": visitor.coming_from.company_name if visitor.coming_from else '',
            "visiting_date": visitor.visiting_date,
            "visiting_time": visitor.visiting_time,
            "approve_url": approve_url,
            "reject_url": reject_url
        }

        subject = f"[Approval Required] Visitor: {visitor.visitor_name}"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [host.email] if host else []

        # Render email content (we'll create the templates next)
        text_content = render_to_string("emails/visitor_approval.txt", context)
        html_content = render_to_string("emails/visitor_approval.html", context)

        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    except Visitor.DoesNotExist:
        pass
