from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.utils import timezone
from user_onboarding.models import Company
from django.conf import settings
import qrcode
from io import BytesIO
from django.core.files import File


class Category(models.Model):
    """Category model for visitor types"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories' 
    
    def __str__(self):
        return self.name   





import uuid


class TimestampedModel(models.Model):
    """Base model with common timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True

class UUIDModel(models.Model):
    """Base model with UUID primary key"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    class Meta:
        abstract = True




class Vehicle(UUIDModel, TimestampedModel):
    """Vehicle model with better validation"""
    
    class VehicleType(models.TextChoices):
        CAR = 'CAR', 'Car'
        BIKE = 'BIKE', 'Bike'
        BUS = 'BUS', 'Bus'
        TRUCK = 'TRUCK', 'Truck'
        OTHER = 'OTHER', 'Other'
    
    vehicle_number = models.CharField(max_length=20, unique=True, db_index=True)
    vehicle_type = models.CharField(max_length=10, choices=VehicleType.choices)
    model = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=50, blank=True)
    owner_name = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'vehicles'
        ordering = ['vehicle_number']
    
    def __str__(self):
        return f"{self.vehicle_number} ({self.get_vehicle_type_display()})"



from django.core.exceptions import ValidationError
from datetime import timedelta, datetime
# from .services import QRCodeService
from .models import UUIDModel, TimestampedModel
import secrets
# from visitors.models import Category, Vehicle

def generate_otp(length=6):
        return ''.join(secrets.choice('0123456789') for _ in range(length))
class VisitorManager(models.Manager):
    """Custom manager for Visitor model"""

    def active(self):
        return self.filter(is_active=True)

    def pending_approval(self):
        return self.filter(status=Visitor.PassStatus.PENDING)

    def approved(self):
        return self.filter(status=Visitor.PassStatus.APPROVED)

    def currently_inside(self):
        return self.filter(is_inside=True)

    def for_date(self, date):
        return self.filter(visiting_date=date)


class Visitor(UUIDModel, TimestampedModel):
    """Visitor model with smart pass management"""

    class PassType(models.TextChoices):
        ONE_TIME = 'ONE_TIME', 'One Time'
        RECURRING = 'RECURRING', 'Recurring'
        # PERMANENT = 'PERMANENT', 'Permanent'

    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'
        PREFER_NOT_TO_SAY = 'P', 'Prefer not to say'

    class PassStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        EXPIRED = 'EXPIRED', 'Expired'
        CANCELLED = 'CANCELLED', 'Cancelled'
        # BLACKLISTED = 'BLACKLISTED', 'Blacklisted'

    # Basic Info
    pass_id = models.CharField(max_length=20, unique=True, editable=False, db_index=True)
    visitor_name = models.CharField(max_length=255, db_index=True)
    mobile_number = models.CharField(max_length=15, db_index=True)
    email_id = models.EmailField(blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices)
    photo = models.ImageField(upload_to='visitor_photos/', null=True, blank=True)

    # Visit Details
    pass_type = models.CharField(max_length=20, choices=PassType.choices, default=PassType.ONE_TIME)
    visiting_date = models.DateField(db_index=True)
    visiting_time = models.TimeField()
    valid_until = models.DateTimeField(null=True, blank=True)
    recurring_days = models.PositiveIntegerField(null=True, blank=True)
    allowing_hours = models.PositiveIntegerField(default=8)

    # Relationships
    category = models.ForeignKey('add_visitors.Category', on_delete=models.PROTECT, related_name='visitors_all')
    whom_to_meet = models.CharField(max_length=255, blank=True)
    host_employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='hosted_visitors'
    )

    coming_from = models.TextField(max_length=250, blank=True, null=True)
   
    is_active = models.BooleanField(default=True)
    purpose_of_visit = models.TextField()
    belongings_tools = models.TextField(blank=True)
    security_notes = models.TextField(blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)

    # Status & Approval
    status = models.CharField(max_length=20, choices=PassStatus.choices, default=PassStatus.PENDING)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='visitors_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Entry/Exit Tracking
    entry_time = models.DateTimeField(null=True, blank=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    is_inside = models.BooleanField(default=False)

    # QR Code & Documents
    qr_code = models.ImageField(upload_to='visitor_qrcodes/', null=True, blank=True)
    id_document = models.FileField(upload_to='visitor_documents/', null=True, blank=True)

    # Audit Trail
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='visitors_created'
    )
    entry_time = models.DateTimeField(null=True, blank=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    is_inside = models.BooleanField(default=False)

    # OTP Fields ✅
    entry_otp = models.CharField(max_length=128, null=True, blank=True)
    exit_otp = models.CharField(max_length=128, null=True, blank=True)

    objects = VisitorManager()

    class Meta:
        db_table = 'visitors'
        ordering = ['-visiting_date', '-visiting_time']
        indexes = [
            models.Index(fields=['visiting_date', 'status']),
            models.Index(fields=['mobile_number', 'visiting_date']),
            models.Index(fields=['status', 'is_inside']),
        ]

    def clean(self):
        if self.visiting_date and self.visiting_date < timezone.now().date():
            raise ValidationError({'visiting_date': 'Visiting date cannot be in the past'})
        if self.pass_type == self.PassType.RECURRING and not self.recurring_days:
            raise ValidationError({'recurring_days': 'Recurring days required for recurring pass'})

    def save(self, *args, **kwargs):
        if not self.pass_id:
            self.pass_id = self._generate_pass_id()

        if not self.valid_until:
            visiting_datetime = datetime.combine(self.visiting_date, self.visiting_time)
            if self.pass_type == self.PassType.RECURRING and self.recurring_days:
                self.valid_until = timezone.make_aware(visiting_datetime + timedelta(days=self.recurring_days))
            elif self.pass_type == self.PassType.ONE_TIME:
                self.valid_until = timezone.make_aware(visiting_datetime + timedelta(hours=self.allowing_hours))

        self.full_clean()
        super().save(*args, **kwargs)

        if not self.qr_code:
            self._generate_qr_code()
    

    def _generate_pass_id(self):
        import random, string
        date_str = timezone.now().strftime('%y%m%d')
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"VP{date_str}{random_str}"

    def _generate_qr_code(self):
        from .services import QRCodeService
        qr_service = QRCodeService()
        qr_service.generate_visitor_qr(self)

    @property
    def allowed_entry_until(self):
        dt = datetime.combine(self.visiting_date, self.visiting_time)
        return timezone.make_aware(dt + timedelta(hours=self.allowing_hours))

    @property
    def is_expired(self):
        if self.pass_type == self.PassType.PERMANENT:
            return False
        return timezone.now() > self.allowed_entry_until

    @property
    def can_enter(self):
        return (
            self.status == self.PassStatus.APPROVED and
            not self.is_expired and
            not self.is_inside and
            timezone.now() >= timezone.make_aware(datetime.combine(self.visiting_date, self.visiting_time))
        )
   

   



    def __str__(self):
        return f"{self.visitor_name} - {self.pass_id}"


class VisitorLog(UUIDModel, TimestampedModel):
    """Log for all visitor entry/exit actions"""

    class Action(models.TextChoices):
        ENTRY = 'ENTRY', 'Entry'
        EXIT = 'EXIT', 'Exit'
        REJECTED_ENTRY = 'REJECTED_ENTRY', 'Rejected Entry'
        EMERGENCY_EXIT = 'EMERGENCY_EXIT', 'Emergency Exit'

    # class Gate(models.TextChoices):
    #     MAIN_GATE = 'MAIN', 'Main Gate'
    #     SIDE_GATE = 'SIDE', 'Side Gate'
    #     EMERGENCY_GATE = 'EMERGENCY', 'Emergency Gate'

    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=20, choices=Action.choices)
    # gate = models.CharField(max_length=20, choices=Gate.choices, default=Gate.MAIN_GATE)
    security_guard = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    notes = models.TextField(blank=True)
    device_info = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'visitor_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['visitor', 'action']),
            models.Index(fields=['created_at', 'action']),
        ]

    def __str__(self):
        return f"{self.visitor.visitor_name} - {self.get_action_display()} {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
