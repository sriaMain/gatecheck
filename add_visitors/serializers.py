
from rest_framework import serializers
from .models import Visitor, Category, Vehicle, VisitorLog
from user_onboarding.serializers import CompanySerializer
from user_onboarding.models import Company
from .services import QRCodeService
import logging
logger = logging.getLogger(__name__)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'is_active']
    def validate_name(self, value):
        # case-insensitive duplicate check
        if Category.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Category name already exists.")
        return value

class VehicleSerializer(serializers.ModelSerializer):       
    class Meta:
        model = Vehicle
        fields = ['id', 'vehicle_number', 'vehicle_type', 'model', 'color']

class VisitorLogSerializer(serializers.ModelSerializer):
    security_guard_name = serializers.CharField(source='security_guard.username', read_only=True)
    
    class Meta:
        model = VisitorLog
        fields = ['id', 'action','security_guard_name', 'notes']

class VisitorListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing visitors"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    company_name = serializers.CharField(source='coming_from.name', read_only=True)
    qr_code_url = serializers.SerializerMethodField()
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    class Meta:
        model = Visitor
        fields = [
            'id', 'pass_id', 'visitor_name', 'mobile_number', 'visiting_date', 
            'visiting_time', 'status', 'category_name', 'company_name', 'is_inside', 'qr_code_url', 'email_id', 'pass_type',"created_by"
        ]
    

    def get_qr_code_url(self, obj):
        request = self.context.get('request')
        if not request:
            logger.warning("Request not found in serializer context.")
        if request and obj.qr_code and hasattr(obj.qr_code, 'url'):
            return request.build_absolute_uri(obj.qr_code.url)
        return None
    
    def validate(self, attrs):
        # If not bulk upload, enforce gender
        if not self.context.get('bulk_upload', False):
            if not attrs.get('gender'):
                raise serializers.ValidationError({"gender": "This field is required for manual entry."})
        return attrs

class VisitorDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for visitor CRUD operations"""
    # coming_from = CompanySerializer
    # coming_from = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())
    company_details = serializers.CharField(source='coming_from', read_only=True)

    company = serializers.CharField(
        source="created_by.company.company_name",  # 👈 follow chain
        read_only=True
    )
    category_details = CategorySerializer(source='category', read_only=True)
    # company_details = CompanySerializer(source='coming_from', read_only=True)
    vehicle_details = VehicleSerializer(source='vehicle', read_only=True)
    logs = VisitorLogSerializer(many=True, read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    qr_code_url = serializers.SerializerMethodField()
    can_enter = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    
    def get_created_by_name(self, obj):
        """Get creator name with fallback to username if full name is empty"""
        if obj.created_by:
            full_name = obj.created_by.get_full_name()
            return full_name if full_name else obj.created_by.username
        return None

    
    class Meta:
        model = Visitor
        fields = [
            'id', 'pass_id', 'visitor_name', 'mobile_number', 'email_id', 'gender',
            'pass_type', 'visiting_date', 'visiting_time', 'recurring_days', 'allowing_hours', 'valid_until',
            'category', 'category_details', 'whom_to_meet', 'coming_from', 'company_details',
            'belongings_tools', 'purpose_of_visit', 'vehicle', 'vehicle_details',
            'status', 'approved_by', 'approved_by_name', 'approved_at', 'entry_time', 'exit_time',
            'is_inside', 'created_at', 'created_by_name', 'created_by_email', 'updated_at', 'logs', 'qr_code_url', 'is_expired', 'can_enter', 'company',
        ]
        read_only_fields = ['pass_id', 'valid_until', 'approved_by', 'approved_at', 'entry_time', 'exit_time', 'is_inside', 'can_enter', 'is_expired', 'created_by_name', 'created_by_email']

  
    def get_qr_code_url(self, obj):
        if obj.qr_code and hasattr(obj.qr_code, 'url'):
            qr_url = obj.qr_code.url
            # If it's already a full URL (Cloudinary), return as-is
            if qr_url.startswith('http://') or qr_url.startswith('https://'):
                return qr_url
            # Otherwise, build absolute URI for local files
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(qr_url)
            return qr_url
        return None

    def create(self, validated_data):
        company_data = validated_data.pop('coming_from')
        company = Company.objects.create(**company_data)
        visitor = Visitor.objects.create(coming_from=company, **validated_data)
    # def create(self, validated_data):
    # # coming_from is already a Company instance (foreign key)
    #     coming_from = validated_data.get("coming_from")

    #     # Create visitor only once
    #     visitor = Visitor.objects.create(**validated_data)

    #     # Generate QR Code
    #     QRCodeService().generate_visitor_qr(visitor)

    #     return visitor


    # ✅ Generate QR Code
        QRCodeService().generate_visitor_qr(visitor)
        return Visitor.objects.create(coming_from=company, **validated_data)



class VisitorCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating visitors"""
    email_id = serializers.EmailField(required=True)
    pass_type = serializers.ChoiceField(choices=Visitor.PassType.choices, required=True)
    


    class Meta:
        model = Visitor
        fields = [
            'visitor_name', 'mobile_number', 'email_id', 'gender', 'pass_type',
            'visiting_date', 'visiting_time', 'recurring_days', 'allowing_hours',
            'category', 'whom_to_meet', 'coming_from', 'belongings_tools',
            'purpose_of_visit', 'vehicle'
        ]

    def validate_mobile_number(self, value):
        """Validate mobile number format"""
        if not value.isdigit() or len(value) < 10:
            raise serializers.ValidationError("Mobile number must be at least 10 digits")
        return value

    def validate_visiting_date(self, value):
        """Ensure visiting date is not in the past"""
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("Visiting date cannot be in the past")
        return value
    
    def validate_category(self, value):
        """Ensure category is active"""
        if not value.is_active:
            raise serializers.ValidationError(f"Category '{value.name}' is inactive and cannot be used.")
        return value




