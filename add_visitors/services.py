from django.utils import timezone
from django.db import transaction
from typing import Dict, List, Optional
from .models import Visitor, VisitorLog
# from .services import NotificationService
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import generate_otp


class VisitorService:
    def __init__(self):
        self.notification_service = NotificationService()

    @transaction.atomic
    def create_visitor(self, visitor_data: Dict, created_by) -> Visitor:
        visitor = Visitor.objects.create(**visitor_data, created_by=created_by)
        if visitor.host_employee:
            self.notification_service.notify_host_of_visitor_request(visitor)
        return visitor

    

    @transaction.atomic
    def approve_visitor(self, visitor_id: str, approved_by) -> Visitor:
        visitor = Visitor.objects.get(id=visitor_id)

        # ✅ Generate OTPs
        visitor.entry_otp = generate_otp()
        visitor.exit_otp = generate_otp()

        visitor.status = Visitor.PassStatus.APPROVED
        visitor.approved_by = approved_by
        visitor.approved_at = timezone.now()

        # ✅ Save everything in one go
        visitor.save(update_fields=[
            'status', 'approved_by', 'approved_at',
            'entry_otp', 'exit_otp'
        ])

        # ✅ Trigger notification email (includes OTPs now)
        self.notification_service.notify_visitor_approval(visitor)
        return visitor

        

    @transaction.atomic
    def reject_visitor(self, visitor_id: str, reason: str, rejected_by) -> Visitor:
        visitor = Visitor.objects.get(id=visitor_id)
        visitor.status = Visitor.PassStatus.REJECTED
        visitor.rejection_reason = reason
        visitor.approved_by = rejected_by
        visitor.approved_at = timezone.now()
        visitor.save(update_fields=['status', 'rejection_reason', 'approved_by', 'approved_at'])
        self.notification_service.notify_visitor_rejection(visitor)
        return visitor

    @transaction.atomic
    def record_entry(self, visitor_id: str, gate: str, security_guard, notes: str = "") -> VisitorLog:
        visitor = Visitor.objects.get(id=visitor_id)
        if not visitor.can_enter:
            raise ValueError("Visitor cannot enter at this time")
        visitor.entry_time = timezone.now()
        visitor.is_inside = True
        visitor.save(update_fields=['entry_time', 'is_inside'])
        log = VisitorLog.objects.create(
            visitor=visitor,
            action=VisitorLog.Action.ENTRY,
            gate=gate,
            security_guard=security_guard,
            notes=notes
        )
        if visitor.host_employee:
            self.notification_service.notify_host_of_visitor_arrival(visitor)
        return log

    @transaction.atomic
    def record_exit(self, visitor_id: str, gate: str, security_guard, notes: str = "") -> VisitorLog:
        visitor = Visitor.objects.get(id=visitor_id)
        if not visitor.is_inside:
            raise ValueError("Visitor is not currently inside")
        visitor.exit_time = timezone.now()
        visitor.is_inside = False
        visitor.save(update_fields=['exit_time', 'is_inside'])
        log = VisitorLog.objects.create(
            visitor=visitor,
            action=VisitorLog.Action.EXIT,
            gate=gate,
            security_guard=security_guard,
            notes=notes
        )
        return log

    def get_visitors_for_approval(self, user) -> List[Visitor]:
        return Visitor.objects.pending_approval().filter(
            host_employee=user
        ).select_related('category', 'coming_from', 'vehicle')

    def get_dashboard_stats(self) -> Dict:
        today = timezone.now().date()
        return {
            'total_visitors_today': Visitor.objects.for_date(today).count(),
            'approved_today': Visitor.objects.for_date(today).approved().count(),
            'pending_approval': Visitor.objects.pending_approval().count(),
            'currently_inside': Visitor.objects.currently_inside().count(),
            'total_entries_today': VisitorLog.objects.filter(
                created_at__date=today,
                action=VisitorLog.Action.ENTRY
            ).count(),
        }

# visitors/services/qr_service.py
import qrcode
import json
from io import BytesIO
from django.core.files import File
from django.conf import settings
from django.core.files.base import ContentFile

# class QRCodeService:
#     def generate_visitor_qr(self, visitor):
#         """Generate QR code for visitor pass"""
#         try:
#         qr_data = {
#             'visitor_id': str(visitor.id),
#             'pass_id': visitor.pass_id,
#             'valid_until': visitor.valid_until.isoformat() if visitor.valid_until else None,
#             "entry_time": visitor.entry_time.isoformat() if visitor.entry_time else None,
#             "exit_time": visitor.exit_time.isoformat() if visitor.exit_time else None
#         }
#         qr.add_data(json.dumps(qr_data))
#         qr = qrcode.QRCode(version=1, box_size=10, border=5)
#         # qr.add_data(str(qr_data))
#         qr.make(fit=True)
        
#         img = qr.make_image(fill_color="black", back_color="white")
#         buffer = BytesIO()
#         img.save(buffer, format='PNG')
        
#         filename = f"qr_{visitor.pass_id}.png"
#         visitor.qr_code.save(filename, ContentFile(buffer.getvalue()), save=True)
#         return visitor.qr_code
#     except Exception as e:
#             print("❌ Error generating QR code:", e)
#             raise e
    

# import json
# import qrcode
# from io import BytesIO
# from django.core.files.base import ContentFile

class QRCodeService:
    def generate_visitor_qr(self, visitor):
        """Generate professional QR code for visitor pass"""
        try:
            # qr_data_url = f"http://127.0.0.1:8000/visitor-pass/{visitor.id}/"
            qr_data = {
                "visitor_id": str(visitor.id),
                "pass_id": visitor.pass_id,
                "valid_until": visitor.valid_until.isoformat() if visitor.valid_until else None,
                "entry_time": visitor.entry_time.isoformat() if visitor.entry_time else None,
                "exit_time": visitor.exit_time.isoformat() if visitor.exit_time else None
            }

            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            # qr.add_data(qr_data_url)
            qr.add_data(json.dumps(qr_data))  # ✅ Proper JSON
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')

            filename = f"qr_{visitor.pass_id}.png"
            visitor.qr_code.save(filename, ContentFile(buffer.getvalue()), save=True)
            return visitor.qr_code

        except Exception as e:
            print("❌ Error generating QR code:", e)
            raise e


# visitors/services/notification_service.py
from django.template.loader import render_to_string
from .tasks import send_email_task  # ✅ Import task directly

class NotificationService:
    def notify_visitor_approval(self, visitor):
        if visitor.email_id:
            context = {
                'visitor': visitor,
                'qr_code_url': visitor.qr_code.url if visitor.qr_code else None,
            }
            subject = f"Gate Pass Approved - {visitor.pass_id}"
            html_message = render_to_string('emails/visitor_approved.html', context)
            plain_message = render_to_string('emails/visitor_approved.txt', context)

            send_email_task.delay(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                recipient_list=[visitor.email_id]
            )

    def notify_host_of_visitor_request(self, visitor):
        if visitor.host_employee and visitor.host_employee.email:
            context = {'visitor': visitor}
            subject = f"Visitor Request - {visitor.visitor_name}"
            html_message = render_to_string('emails/host_visitor_request.html', context)
            plain_message = render_to_string('emails/host_visitor_request.txt', context)

            send_email_task.delay(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                recipient_list=[visitor.host_employee.email]
            )

    def notify_visitor_rejection(self, visitor):
        if visitor.email_id:
            context = {
                'visitor': visitor,
            }
            subject = f"Gate Pass Rejected - {visitor.pass_id}"
            html_message = render_to_string('emails/visitor_rejected.html', context)
            plain_message = render_to_string('emails/visitor_rejected.txt', context)

            send_email_task.delay(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                recipient_list=[visitor.email_id]
            )


# Add this method to NotificationService class
def notify_host_of_visitor_arrival(self, visitor):
    """Notify host when visitor actually arrives at gate"""
    if visitor.host_employee and visitor.host_employee.email:
        context = {
            'visitor': visitor,
            'arrival_time': visitor.entry_time,
            'gate': visitor.visitorlog_set.filter(action='ENTRY').last().gate
        }
        subject = f"Visitor Arrived - {visitor.visitor_name}"
        html_message = render_to_string('emails/visitor_arrival.html', context)
        plain_message = render_to_string('emails/visitor_arrival.txt', context)
        send_email_task.delay(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            recipient_list=[visitor.host_employee.email]
        )

