from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from datetime import date

from .models import Visitor, Company, Category, Vehicle, VisitorLog
from .serializers import (
    VisitorListSerializer, VisitorDetailSerializer, VisitorCreateUpdateSerializer,
     CategorySerializer, VehicleSerializer, VisitorLogSerializer
)
from django.contrib.auth.hashers import make_password
from add_visitors.models import generate_otp
from rest_framework_simplejwt.authentication import JWTAuthentication 
from rest_framework.permissions import IsAdminUser
from django.db import transaction
from datetime import datetime
from add_visitors.tasks import send_visit_scheduled_email
from .services import QRCodeService
from django.core.paginator import Paginator

from rest_framework import status
import logging

logger = logging.getLogger(__name__)

class BaseAPIView(APIView):
    """Base API view with common functionality"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]  # Set your authentication classes here if needed
    
    
    def get_paginated_response(self, queryset, serializer_class, request):
        """Helper method for pagination"""
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = serializer_class(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = serializer_class(queryset, many=True)
        return Response(serializer.data)

from add_visitors.models import generate_otp


class VisitorListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication] 
    

    def get(self, request):
        self.permission_required = "view_visitors"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        user_company = getattr(request.user, 'company', None)
        if request.user.is_superuser:
            queryset = Visitor.objects.filter(is_active=True).order_by('-created_at')
        elif user_company and request.user.is_staff:
            queryset = Visitor.objects.filter(
                created_by__company=user_company,
                is_active=True
            ).order_by('-created_at')
        else:
            queryset = Visitor.objects.filter(
                created_by=request.user,
                is_active=True
            ).order_by('-created_at')

        search = request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(

                Q(visitor_name__icontains=search) |
                Q(mobile_number__icontains=search) |
                Q(pass_id__icontains=search)
            )
        # return Response(VisitorListSerializer(queryset, many=True).data)
        # VisitorListSerializer(queryset, many=True, context={'request': request}).data
        serializer = VisitorListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

  

    def post(self, request):

        self.permission_required = "create_visitor"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = VisitorCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    visitor = serializer.save(created_by=request.user)

                    # -------------------------------------------
                    # ✅ AUTO APPROVE LOGIC BASED ON visiting_date
                    # -------------------------------------------
                    from datetime import date

                    visiting_date = visitor.visiting_date   # <-- correct field
                    today = date.today()

                    if visiting_date > today:
                        visitor.status = "APPROVED"   # Future date → auto approve
                    else:
                        visitor.status = "PENDING"    # Today → pending approval

                    visitor.save()
                    # -------------------------------------------

                    # Generate OTPs
                    entry_otp_plain = generate_otp()
                    exit_otp_plain = generate_otp()

                    visitor.entry_otp = make_password(entry_otp_plain)
                    visitor.exit_otp = make_password(exit_otp_plain)
                    visitor.save()

                    logger.info(f"Visitor saved with ID: {visitor.id}")
                    QRCodeService().generate_visitor_qr(visitor)

                    # transaction.on_commit(lambda: send_visit_scheduled_email.apply_async(
                    #     args=[str(visitor.id), entry_otp_plain, exit_otp_plain],
                    #     countdown=2
                    # ))
                    # Direct email sending (no Celery)
                    send_visit_scheduled_email(str(visitor.id), entry_otp_plain, exit_otp_plain)


                    response_data = VisitorDetailSerializer(visitor, context={'request': request}).data
                    response_data['message'] = 'Visitor created successfully'
                    response_data['email_status'] = "Visit scheduled email task triggered"

                    return Response(response_data, status=status.HTTP_201_CREATED)

            except Exception as e:
                logger.error(f"Error creating visitor: {str(e)}")
                return Response(
                    {'error': 'Failed to create visitor. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





from rest_framework.exceptions import PermissionDenied
class VisitorDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    # def get_object(self, pk,request):
    #     self.permission_required = "view_visitors"
    #     if not HasRolePermission().has_permission(request, self.permission_required):
    #         return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    #     return get_object_or_404(Visitor, pk=pk, is_active=True)

    # def get(self, request, pk):
    #     self.permission_required = "view_visitors"
    #     if not HasRolePermission().has_permission(request, self.permission_required):
    #         return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    #     visitor = self.get_object(pk)
    #     serializer = VisitorListSerializer(visitor, context={'request': request})
    #     return Response(serializer.data)
    def get_object(self, request, pk):
    # Permission check
        self.permission_required = "view_visitors"
        if not HasRolePermission().has_permission(request, self.permission_required):
            raise PermissionDenied("Permission denied.")

        # Return the visitor if found
        return get_object_or_404(Visitor, pk=pk, is_active=True)

    def get(self, request, pk):
        visitor = self.get_object(request, pk)  # ✅ pass request + pk
        serializer = VisitorListSerializer(visitor, context={'request': request})
        return Response(serializer.data)

    def put(self, request, pk):
        self.permission_required = "update_visitors"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        visitor = self.get_object(request, pk)
        if visitor.status in ['APPROVED', 'REJECTED']:
            return Response({'error': 'Cannot update approved or rejected visitor'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = VisitorCreateUpdateSerializer(visitor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(VisitorDetailSerializer(visitor).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        self.permission_required = "delete_visitors"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        visitor = self.get_object(pk)
        visitor.is_active = False
        visitor.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    




# class VisitorRescheduleAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [JWTAuthentication]
    

    # def post(self, request, pk):
    #     self.permission_required = "create_reschedule"
    #     if not HasRolePermission().has_permission(request, self.permission_required):
    #         return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    #     visitor = get_object_or_404(Visitor, pk=pk, is_active=True)

    #     # Prevent rescheduling if visitor has already entered or is currently inside
    #     if visitor.entry_time is not None or visitor.is_inside:
    #         return Response(
    #             {"error": "Visitor has already entered. Rescheduling not allowed."},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     new_date = request.data.get("new_date")
    #     new_time = request.data.get("new_time")

    #     if not new_date or not new_time:
    #         return Response(
    #             {"error": "Both 'new_date' and 'new_time' are required."},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     # Parse date and time strings
    #     try:
    #         new_date_obj = datetime.strptime(new_date, "%Y-%m-%d").date()
    #         new_time_obj = datetime.strptime(new_time, "%H:%M:%S").time()
    #     except ValueError:
    #         return Response(
    #             {"error": "Invalid date or time format. Use YYYY-MM-DD and HH:MM:SS."},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     # Check that the new date is today or in the future
    #     if new_date_obj < localdate():
    #         return Response(
    #             {"error": "New visiting date must be today or in the future."},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     try:
    #         with transaction.atomic():
    #             # Update visitor with new schedule
    #             visitor.visiting_date = new_date_obj
    #             visitor.visiting_time = new_time_obj
    #             visitor.valid_until = None
    #             visitor.modified_by = request.user
    #             visitor.save()

    #             otp_sent = False

    #             # Log dates to help debugging
    #             logger.info(f"Rescheduling visitor pass {visitor.pass_id} to {new_date_obj} {new_time_obj}")
    #             logger.info(f"Current local date: {localdate()}")

    #             # Regenerate and send OTP only if the new date is today (local timezone)
    #             if new_date_obj == localdate():
    #                 # Generate new OTPs for entry and exit
    #                 entry_otp_plain = generate_otp()
    #                 exit_otp_plain = generate_otp()

    #                 # Hash and save generated OTPs
    #                 visitor.entry_otp = make_password(entry_otp_plain)
    #                 visitor.exit_otp = make_password(exit_otp_plain)
    #                 visitor.save()

    #                 # Schedule sending OTP via Celery after transaction commits
    #                 transaction.on_commit(lambda: send_visit_scheduled_email.apply_async(
    #                     args=[str(visitor.id), entry_otp_plain, exit_otp_plain],
    #                     countdown=2
    #                 ))

    #                 otp_sent = True

    #             return Response({
    #                 "message": "Visitor pass rescheduled successfully.",
    #                 "new_date": str(visitor.visiting_date),
    #                 "new_time": str(visitor.visiting_time),
    #                 "pass_id": visitor.pass_id,
    #                 "otp_sent": otp_sent
    #             }, status=status.HTTP_200_OK)

    #     except Exception as e:
    #         logger.error(f"Reschedule error for visitor pass {pk}: {str(e)}", exc_info=True)
    #         return Response(
    #             {"error": "Failed to reschedule visitor. Please try again."},
    #             status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #         )

   

    # def post(self, request, pk):
    #         self.permission_required = "create_reschedule"
    #         if not HasRolePermission().has_permission(request, self.permission_required):
    #             return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    #         visitor = get_object_or_404(Visitor, pk=pk, is_active=True)

    #         # Prevent rescheduling after entering
    #         if visitor.entry_time is not None or visitor.is_inside:
    #             return Response(
    #                 {"error": "Visitor has already entered. Rescheduling not allowed."},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )

    #         new_date = request.data.get("new_date")
    #         new_time = request.data.get("new_time")

    #         if not new_date or not new_time:
    #             return Response(
    #                 {"error": "Both 'new_date' and 'new_time' are required."},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )

    #         try:
    #             new_date_obj = datetime.strptime(new_date, "%Y-%m-%d").date()
    #             new_time_obj = datetime.strptime(new_time, "%H:%M:%S").time()
    #         except ValueError:
    #             return Response(
    #                 {"error": "Invalid date or time format. Use YYYY-MM-DD and HH:MM:SS."},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )

    #         if new_date_obj < localdate():
    #             return Response(
    #                 {"error": "New visiting date must be today or in the future."},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )

    #         try:
    #             with transaction.atomic():

    #                 # Update schedule
    #                 visitor.visiting_date = new_date_obj
    #                 visitor.visiting_time = new_time_obj
    #                 visitor.valid_until = None
    #                 visitor.modified_by = request.user

    #                 # ALWAYS generate OTP — even for future
    #                 entry_otp_plain = generate_otp()
    #                 exit_otp_plain = generate_otp()

    #                 visitor.entry_otp = make_password(entry_otp_plain)
    #                 visitor.exit_otp = make_password(exit_otp_plain)

    #                 visitor.save()

    #                 # Always send email
    #                 transaction.on_commit(lambda: send_visit_scheduled_email(
    #                     args=[str(visitor.id), entry_otp_plain, exit_otp_plain],
    #                     countdown=1
    #                 ))

    #                 return Response({
    #                     "message": "Visitor pass rescheduled successfully.",
    #                     "new_date": str(visitor.visiting_date),
    #                     "new_time": str(visitor.visiting_time),
    #                     "pass_id": visitor.pass_id,
    #                     "otp_sent": True
    #                 }, status=status.HTTP_200_OK)

    #         except Exception as e:
    #             logger.error(f"Reschedule error: {str(e)}", exc_info=True)
    #             return Response(
    #                 {"error": f"Failed to reschedule visitor: {str(e)}"},
    #                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #             )

class VisitorRescheduleAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, pk):
        self.permission_required = "create_reschedule"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        visitor = get_object_or_404(Visitor, pk=pk, is_active=True)

        # Prevent rescheduling if visitor has already entered
        if visitor.entry_time is not None or visitor.is_inside:
            return Response(
                {"error": "Visitor has already entered. Rescheduling not allowed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_date = request.data.get("new_date")
        new_time = request.data.get("new_time")

        if not new_date or not new_time:
            return Response(
                {"error": "Both 'new_date' and 'new_time' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parse date/time
        try:
            new_date_obj = datetime.strptime(new_date, "%Y-%m-%d").date()
            new_time_obj = datetime.strptime(new_time, "%H:%M:%S").time()
        except ValueError:
            return Response(
                {"error": "Invalid date or time format. Use YYYY-MM-DD and HH:MM:SS."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_date_obj < localdate():
            return Response(
                {"error": "New visiting date must be today or future."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():

                # Update schedule
                visitor.visiting_date = new_date_obj
                visitor.visiting_time = new_time_obj
                visitor.valid_until = None
                visitor.modified_by = request.user

                # ALWAYS generate OTP
                entry_otp_plain = generate_otp()
                exit_otp_plain = generate_otp()

                visitor.entry_otp = make_password(entry_otp_plain)
                visitor.exit_otp = make_password(exit_otp_plain)
                visitor.save()

                # SEND EMAIL DIRECTLY (NO CELERY)
                send_visit_scheduled_email(
                    visitor.id,
                    entry_otp_plain,
                    exit_otp_plain
                )

                return Response({
                    "message": "Visitor pass rescheduled successfully.",
                    "new_date": str(visitor.visiting_date),
                    "new_time": str(visitor.visiting_time),
                    "pass_id": visitor.pass_id,
                    "otp_sent": True
                }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Reschedule Error: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Failed to reschedule visitor: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )





from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

class VisitorApprovalAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, pk):
        self.permission_required = "create_approval"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        visitor = get_object_or_404(Visitor, pk=pk, is_active=True)
        action = request.data.get('action')
        rejection_reason = request.data.get('rejection_reason', '')

        if action not in ['approve', 'reject']:
            return Response({'error': 'Invalid action. Use "approve" or "reject".'},
                            status=status.HTTP_400_BAD_REQUEST)

        if visitor.status != Visitor.PassStatus.PENDING:
            return Response({'error': f'Cannot {action} visitor with status {visitor.status}'},
                            status=status.HTTP_400_BAD_REQUEST)

        if action == 'approve':
            visitor.status = Visitor.PassStatus.APPROVED
            visitor.rejection_reason = ''
        else:
            visitor.status = Visitor.PassStatus.REJECTED
            visitor.rejection_reason = rejection_reason or "Rejected by host"

        visitor.approved_by = request.user
        visitor.approved_at = timezone.now()

        # ✅ Catch validation errors (e.g., visiting date is in the past)
        try:
            visitor.save()
        except ValidationError as e:
            # Extract error messages cleanly
            errors = {field: [str(msg) for msg in msgs] for field, msgs in e.message_dict.items()}
            return Response({'validation_error': errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            VisitorDetailSerializer(visitor, context={'request': request}).data,
            status=status.HTTP_200_OK
        )

from django.views import View
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Visitor
from roles_creation.permissions import HasRolePermission
class VisitorApprovalDecisionView(View):
    template_name = "visitor_approval_result.html"

    def get(self, request, pk):
        self.permission_required = "view_approval"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        action = request.GET.get("action")
        visitor = get_object_or_404(Visitor, pk=pk, is_active=True)

        if visitor.status != Visitor.PassStatus.PENDING:
            return render(request, self.template_name, {
                "message": f"This visitor has already been {visitor.status.lower()}."
            })

        if action == "approve":
            visitor.status = Visitor.PassStatus.APPROVED
            visitor.rejection_reason = ''
            message = "✅ You have successfully approved the visitor."
        elif action == "reject":
            visitor.status = Visitor.PassStatus.REJECTED
            visitor.rejection_reason = "Rejected via email link"
            message = "❌ You have rejected the visitor."
        else:
            message = "❗ Invalid action."

        visitor.approved_at = timezone.now()
        visitor.save()

        return render(request, self.template_name, {
            "message": message
        })






from datetime import datetime
import pytz
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import check_password
from add_visitors.models import Visitor, VisitorLog
from add_visitors.serializers import VisitorDetailSerializer

class VisitorEntryExitView(APIView):
    """
    API to handle visitor check-in (entry) and check-out (exit) with OTP verification.
    OTP is invalidated after successful use to prevent reuse.
    """
    permission_classes = []  # Add authentication if needed

    def post(self, request, pass_id):
        # Get visitor
        visitor = get_object_or_404(Visitor, pass_id=pass_id, is_active=True)

        action = request.data.get('action')   # 'entry' or 'exit'
        otp = request.data.get('otp')         # OTP entered by visitor
        notes = request.data.get('notes', '')

        # Validate action
        if action not in ['entry', 'exit']:
            return Response({'error': 'Action must be either "entry" or "exit"'}, status=status.HTTP_400_BAD_REQUEST)

        # Only approved visitors
        if visitor.status != Visitor.PassStatus.APPROVED:
            return Response({'error': 'Only approved visitors can enter/exit'}, status=status.HTTP_400_BAD_REQUEST)

        # Handle timezone (IST)
        ist = pytz.timezone('Asia/Kolkata')
        scheduled_naive = datetime.combine(visitor.visiting_date, visitor.visiting_time)
        scheduled_ist = ist.localize(scheduled_naive)  # Scheduled visiting time in IST
        now_ist = timezone.now().astimezone(ist)       # Current time in IST

        if action == 'entry':
            if visitor.is_inside:
                return Response({'error': 'Visitor has already checked in.'}, status=status.HTTP_400_BAD_REQUEST)

            # OTP validation (check this FIRST before time validation)
            if not visitor.entry_otp:
                return Response({'error': 'Entry OTP not generated or already used.'}, status=status.HTTP_400_BAD_REQUEST)
            if not check_password(otp, visitor.entry_otp):
                return Response({'error': 'Invalid entry OTP'}, status=status.HTTP_400_BAD_REQUEST)

            # Prevent early check-in (after OTP is validated)
            if now_ist < scheduled_ist:
                return Response({'error': 'Visitor cannot check in before the scheduled visiting time.'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Record entry
            visitor.entry_time = timezone.now()
            visitor.is_inside = True
            # Invalidate OTP only for ONE_TIME passes
            if visitor.pass_type == Visitor.PassType.ONE_TIME:
                visitor.entry_otp = None

        elif action == 'exit':
            if not visitor.is_inside:
                return Response({'error': 'Visitor has not checked in yet or already checked out.'}, status=status.HTTP_400_BAD_REQUEST)

            # OTP validation
            if not visitor.exit_otp:
                return Response({'error': 'Exit OTP not generated or already used.'}, status=status.HTTP_400_BAD_REQUEST)
            if not check_password(otp, visitor.exit_otp):
                return Response({'error': 'Invalid exit OTP'}, status=status.HTTP_400_BAD_REQUEST)

            # Record exit
            visitor.exit_time = timezone.now()
            visitor.is_inside = False
            # Invalidate OTP only for ONE_TIME passes
            if visitor.pass_type == Visitor.PassType.ONE_TIME:
                visitor.exit_otp = None

        # Save visitor
        visitor.save()

        # Log action
        VisitorLog.objects.create(
            visitor=visitor,
            action=action.upper(),
            security_guard=request.user if request.user.is_authenticated else None,
            notes=notes
        )

        serializer = VisitorDetailSerializer(visitor)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CategoryListAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication] 
    """API view for managing categories"""
    
    def get(self, request):
        """List all categories"""
        self.permission_required = "view_category"
        if not HasRolePermission.has_permission(self, request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        categories = Category.objects.filter()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new category"""
        self.permission_required = "create_category"
        if not HasRolePermission.has_permission(self, request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        """Update an existing category"""
        self.permission_required = "update_category"
        if not HasRolePermission.has_permission(self, request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        
        category = get_object_or_404(Category, pk=pk)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):

        """Delete a category"""
        self.permission_required = "delete_category"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        category = get_object_or_404(Category, pk=pk, is_active=True)
        category.is_active = False
        category.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class VehicleListAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication] 
    """API view for managing vehicles"""
    

    def get(self, request, uuid=None):
        if uuid:
            """Retrieve single vehicle by UUID"""
            vehicle = get_object_or_404(Vehicle, pk=uuid, is_active=True)
            serializer = VehicleSerializer(vehicle)
            return Response(serializer.data)
        else:
            """List all vehicles with optional search"""
            vehicles = Vehicle.objects.filter(is_active=True)
            search = request.query_params.get('search', '')
            if search:
                vehicles = vehicles.filter(vehicle_number__icontains=search)
            
            serializer = VehicleSerializer(vehicles, many=True)
            return Response(serializer.data)

    
    def post(self, request):
        """Create a new vehicle"""
        serializer = VehicleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, uuid):
        """Update an existing vehicle"""
        vehicle = get_object_or_404(Vehicle, pk=uuid, is_active=True)
        serializer = VehicleSerializer(vehicle, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, uuid):
        """Delete a vehicle"""
        vehicle = get_object_or_404(Vehicle, pk=uuid, is_active=True)
        vehicle.is_active = False
        vehicle.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

        

class DashboardAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication] 
    """API view for dashboard statistics"""
    
    def get(self, request):
        """Get dashboard statistics"""
        today = timezone.now().date()
        
        stats = {
            'total_visitors_today': Visitor.objects.filter(
                visiting_date=today, is_active=True
            ).count(),
            'pending_approvals': Visitor.objects.filter(
                status='PENDING', is_active=True
            ).count(),
            'visitors_inside': Visitor.objects.filter(
                is_inside=True, is_active=True
            ).count(),
            'total_visitors': Visitor.objects.filter(is_active=True).count(),
            'approved_today': Visitor.objects.filter(
                visiting_date=today, status='APPROVED', is_active=True
            ).count(),      
        }
        
        return Response(stats)

import logging
logger = logging.getLogger(__name__)

# class QRCodeScanAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [JWTAuthentication]
#     def post(self, request):
#         self.permission_required = "create_qr"

#         # 🔐 Permission check
#         if not HasRolePermission().has_permission(request, self.permission_required):
#             return Response(
#                 {"error": "Permission denied"},
#                 status=status.HTTP_403_FORBIDDEN
#             )
#         pass_id = request.data.get("pass_id")

#         if not pass_id:
#             return Response({"error": "pass_id is required"}, status=400)

#         pass_id = pass_id.strip()

#         try:
#             visitor = Visitor.objects.get(pass_id__iexact=pass_id)
#         except Visitor.DoesNotExist:
#             return Response({"error": "Invalid QR or pass ID"}, status=400)

#         # 🚫 Already inside
#         if visitor.is_inside:
#             return Response(
#                 {
#                     "error": "Visitor already checked in",
#                     "status": "Inside",
#                     "entry_time": visitor.entry_time
#                 },
#                 status=400
#             )

#         # 🚫 Inactive pass (optional business rule)
#         if not visitor.is_active:
#             return Response(
#                 {"error": "Visitor pass is inactive"},
#                 status=400
#             )

#         # ✅ Check-in
#         visitor.is_inside = True
#         visitor.entry_time = timezone.now()
#         visitor.save()

        
#         created_by_name = None
#         if visitor.created_by:
#             created_by_name = (
#                 visitor.created_by.get_full_name()
#                 or visitor.created_by.username
#                 or visitor.created_by.email
#             )

#         return Response(
#         {
#             "message": "Visitor checked in successfully",
#             "status": "Inside",
#             "pass_id": visitor.pass_id,
#             "entry_time": visitor.entry_time,

#             "visitor_name": visitor.visitor_name,
#             "email_id": visitor.email_id,
#             "visiting_date": visitor.visiting_date,

#             "category": visitor.category.name if visitor.category else None,
#             "purpose_of_visit": visitor.purpose_of_visit,
#             "phone": visitor.mobile_number,
#             # "coming_from": visitor.coming_from,

#             "created_by": created_by_name,
#             "created_by_id": visitor.created_by.id if visitor.created_by else None,
#         },
#         status=200
#     )

class QRCodeScanAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        self.permission_required = "create_qr"

        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        pass_id = request.data.get("pass_id")

        if not pass_id:
            return Response(
                {"error": "pass_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        pass_id = pass_id.strip()

        try:
            visitor = Visitor.objects.get(pass_id__iexact=pass_id)
        except Visitor.DoesNotExist:
            return Response(
                {"error": "Invalid QR or pass ID"},
                status=status.HTTP_400_BAD_REQUEST
            )

       

        if not visitor.is_inside:
            # Trying to ENTER

            # Prevent check-in before or after scheduled date (only allow on the scheduled date)
            today = timezone.now().date()
            if visitor.visiting_date != today:
                return Response(
                    {"error": "Check-in allowed only on the scheduled visiting date."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ❌ Block re-entry for ONE_TIME pass
            if (
                visitor.pass_type == Visitor.PassType.ONE_TIME
                and visitor.exit_time is not None
            ):
                return Response(
                    {
                        "error": "One-time pass already used. Re-entry not allowed.",
                        "status": "Outside"
                    },
                    status=400
                )

            # ✅ ENTRY
            visitor.is_inside = True
            visitor.entry_time = timezone.now()
            visitor.exit_time = None
            visitor.save()

            action = "ENTRY"
            message = "Visitor checked in successfully"

        else:
            # Trying to EXIT
            visitor.is_inside = False
            visitor.exit_time = timezone.now()
            visitor.save()

            action = "EXIT"
            message = "Visitor checked out successfully"



        # 🧾 Created by fallback
        if visitor.created_by:
            created_by_name = (
                visitor.created_by.get_full_name()
                or visitor.created_by.username
                or visitor.created_by.email
            )
        else:
            created_by_name = None

        return Response(
            {
                "message": message,
                "action": action,            # ENTRY or EXIT
                "status": "Inside" if visitor.is_inside else "Visited",

                "pass_id": visitor.pass_id,
                "visitor_name": visitor.visitor_name,
                "email_id": visitor.email_id,
                "visiting_date": visitor.visiting_date,

                "entry_time": visitor.entry_time,
                "exit_time": visitor.exit_time,
                "purpose_of_visit": visitor.purpose_of_visit,
                "phone": visitor.mobile_number,

                "category": visitor.category.name if visitor.category else None,
                # "coming_from": visitor.coming_from,

                "created_by": created_by_name,
                "created_by_id": visitor.created_by.id if visitor.created_by else None,
            },
            status=status.HTTP_200_OK
        )





from rest_framework.permissions import AllowAny
from django.utils.timezone import localdate
class VisitorFilterAPIView(APIView):
    permission_classes = [AllowAny]
    page_size = 10  

    def get(self, request):
        category = request.GET.get('category')
        pass_type = request.GET.get('pass_type')
        # status_param = request.GET.get('status_param')
        pass_type_param = request.query_params.get('pass_type', None)
        from_date = request.GET.get('from_date')  # Format: YYYY-MM-DD
        to_date = request.GET.get('to_date')      # Format: YYYY-MM-DD
        search = request.GET.get('search')        # For name, email, mobile

        visitors = Visitor.objects.all()

        # Filters
        if category:
            if category.isdigit():
                visitors = visitors.filter(category_id=category)
            else:
                visitors = visitors.filter(category__name__iexact=category)

        if pass_type:
            pass_type = pass_type.replace(" ", "_").upper()
            visitors = visitors.filter(pass_type__icontains=pass_type)
        # # if status_param:
        # # #     visitors = visitors.filter(status__iexact=status_param)
        # if pass_type_param:
        #     visitors = visitors.filter(pass_type__icontains=pass_type_param)
        if from_date and to_date:
            visitors = visitors.filter(visiting_date__range=[from_date, to_date])
        elif from_date:
            visitors = visitors.filter(visiting_date__gte=from_date)
        elif to_date:
            visitors = visitors.filter(visiting_date__lte=to_date)

        # Search (name, email, mobile)
        if search:
            visitors = visitors.filter(
                Q(visitor_name__icontains=search) |
                Q(email_id__icontains=search) |
                Q(mobile_number__icontains=search)
            )

        # Pagination
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 10)
        paginator = Paginator(visitors, page_size)
        try:
            page_obj = paginator.page(page)
        except:
            return Response({'detail': 'Invalid page number'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = VisitorCreateUpdateSerializer(page_obj, many=True)
        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'results': serializer.data
        }, status=status.HTTP_200_OK)
    
# GET /api/visitor-status/<visitor_id>/

from rest_framework import status
from .models import Visitor
from user_onboarding.models import Company
class CompanyVisitorsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]    
    

    def get(self, request, company_id):
        # First, check for the specific permission needed to view visitors.
        self.permission_required = "view_visitors"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied. You do not have the required role.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Find the company the user wants to filter by.
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)

        # Filter visitors that are coming from that company.
        visitors = Visitor.objects.filter(coming_from=company)
        
        # Serialize the data and return it.
        serializer = VisitorDetailSerializer(visitors, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

# visitors/views.py
 # Optional: if you want to secure it

class VerifyVisitorEntryOTPView(APIView):
    # permission_classes = [IsAuthenticated]  # Uncomment if needed
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]  # Allow public access for OTP verification
    def post(self, request):
        from django.contrib.auth.hashers import check_password
        email = request.data.get('email_id')
        otp = request.data.get('entry_otp')

        if not email or not otp:
            return Response({"error": "Email and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            visitor = Visitor.objects.get(email_id=email, is_active=True)
        except Visitor.DoesNotExist:
            return Response({"error": "Visitor not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if already inside
        if visitor.is_inside:
            return Response({"error": "Visitor already checked in"}, status=status.HTTP_400_BAD_REQUEST)

        # Check OTP match using password hash check
        if not check_password(otp, visitor.entry_otp):
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        # Optionally check if visiting date/time is correct
        current_time = timezone.now()
        visit_datetime = timezone.make_aware(
            timezone.datetime.combine(visitor.visiting_date, visitor.visiting_time)
        )
        if current_time < visit_datetime:
            return Response({"error": "Too early for check-in"}, status=status.HTTP_400_BAD_REQUEST)

        # Mark the visitor as checked in
        visitor.is_inside = True
        visitor.entry_time = current_time
        visitor.save()

        # Return full visitor details using VisitorDetailSerializer
        serializer = VisitorDetailSerializer(visitor, context={'request': request})
        return Response({
            "message": "Visitor checked in successfully",
            "visitor": serializer.data
        }, status=status.HTTP_200_OK)


from django.contrib.auth.hashers import check_password


class VerifyVisitorOTPAPIView(APIView):
    

    def post(self, request):
        self.permission_required = "create_qr"

        if not HasRolePermission().has_permission(request, self.permission_required):
                return Response(
                    {"error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN
                )
        otp = request.data.get("otp")
        if not otp:
            return Response(
                {"error": "otp is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        visitor = None
        otp_type = None
        candidates = Visitor.objects.filter(is_active=True)
        for v in candidates:
            if v.entry_otp and check_password(otp, v.entry_otp):
                visitor = v
                otp_type = "entry"
                break
            if v.exit_otp and check_password(otp, v.exit_otp):
                visitor = v
                otp_type = "exit"
                break

        if not visitor:
            return Response(
                {"error": "Invalid OTP"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ENTRY OTP logic
        if otp_type == "entry":
            if visitor.is_inside:
                return Response(
                    {"error": "Visitor already checked in"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            today = timezone.now().date()
            if visitor.visiting_date != today:
                return Response(
                    {"error": "Check-in allowed only on the scheduled visiting date."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if (
                visitor.pass_type == Visitor.PassType.ONE_TIME
                and visitor.exit_time is not None
            ):
                return Response(
                    {
                        "error": "One-time pass already used. Re-entry not allowed.",
                        "status": "Outside"
                    },
                    status=400
                )
            visitor.is_inside = True
            visitor.entry_time = timezone.now()
            visitor.exit_time = None
            visitor.save()
            created_by_name = (
                visitor.created_by.get_full_name()
                if visitor.created_by and visitor.created_by.get_full_name()
                else visitor.created_by.username
                if visitor.created_by
                else None
            )
            return Response(
                {
                    "message": "Visitor checked in successfully",
                    "action": "ENTRY",
                    "visitor": {
                        "pass_id": visitor.pass_id,
                        "visitor_name": visitor.visitor_name,
                        "email_id": visitor.email_id,
                        "mobile_number": visitor.mobile_number,
                        "visiting_date": visitor.visiting_date,
                        "purpose_of_visit": visitor.purpose_of_visit,
                        "is_inside": visitor.is_inside,
                        "entry_time": visitor.entry_time,
                        "exit_time": visitor.exit_time,
                        "category": visitor.category.name if visitor.category else None,
                        "coming_from": visitor.coming_from,
                        "created_by": created_by_name,
                    }
                },
                status=status.HTTP_200_OK
            )

        # EXIT OTP logic
        if otp_type == "exit":
            if visitor.exit_otp_used:
                return Response(
                    {"error": "Exit OTP already used"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not visitor.is_inside:
                return Response(
                    {"error": "Cannot checkout before check-in"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            visitor.is_inside = False
            visitor.exit_time = timezone.now()
            visitor.exit_otp_used = True
            visitor.save()
            created_by_name = (
                visitor.created_by.get_full_name()
                if visitor.created_by and visitor.created_by.get_full_name()
                else visitor.created_by.username
                if visitor.created_by
                else None
            )
            return Response(
                {
                    "message": "Visitor checked out successfully",
                    "action": "EXIT",
                    "visitor": {
                        "pass_id": visitor.pass_id,
                        "visitor_name": visitor.visitor_name,
                        "email_id": visitor.email_id,
                        "mobile_number": visitor.mobile_number,
                        "is_inside": visitor.is_inside,
                        "entry_time": visitor.entry_time,
                        "exit_time": visitor.exit_time,
                        "category": visitor.category.name if visitor.category else None,
                        "purpose_of_visit": visitor.purpose_of_visit,
                        "coming_from": visitor.coming_from,
                        "created_by": created_by_name,
                    }
                },
                status=status.HTTP_200_OK
            )





class VisitorDashboardStatusAPIView(APIView):
    # permission_classes = []  # add auth if needed
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]  # Require authentication

    def get(self, request):
        self.permission_required = "create_qr"

        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        

        # ---------------- COUNTS ----------------
        checked_in_count = Visitor.objects.filter(
            is_inside=True,
            is_active=True
        ).count()

        checked_out_count = Visitor.objects.filter(
            is_inside=False,
            entry_time__isnull=False,
            is_active=True
        ).count()

        on_premises_count = checked_in_count  # same as inside

        # ---------------- LISTS ----------------
        on_premises_visitors = Visitor.objects.filter(
            is_inside=True,
            is_active=True
        ).select_related("category")

        outside_visitors = Visitor.objects.filter(
            is_inside=False,
            entry_time__isnull=False,
            is_active=True
        ).select_related("category")

        return Response(
            {
                "counts": {
                    "checked_in": checked_in_count,
                    "checked_out": checked_out_count,
                    "on_premises": on_premises_count,
                },
                "on_premises_visitors": [
                    {
                        "pass_id": v.pass_id,
                        "visitor_name": v.visitor_name,
                        "mobile_number": v.mobile_number,
                        "category": v.category.name if v.category else None,
                        "entry_time": v.entry_time,
                    }
                    for v in on_premises_visitors
                ],
                "outside_visitors": [
                    {
                        "pass_id": v.pass_id,
                        "visitor_name": v.visitor_name,
                        "exit_time": v.exit_time,
                    }
                    for v in outside_visitors
                ],
            },
            status=status.HTTP_200_OK
        )
    


class VisitorProgressAPIView(APIView):
    # permission_classes = []
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]  # Require authentication

    def get(self, request, pass_id):
        self.permission_required = "create_qr"

        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        visitor = get_object_or_404(Visitor, pass_id=pass_id)

        return Response({
            "pass_id": visitor.pass_id,
            "visitor_name": visitor.visitor_name,
            "status": visitor.status,
            "current_stage": visitor.current_stage,

            "timestamps": {
                # "approved_at": visitor.approved_at,
                "entry_time": visitor.entry_time,
                "exit_time": visitor.exit_time,
            },

            "actions_allowed": {
                "can_check_in": (
                    visitor.status == Visitor.PassStatus.APPROVED
                    and not visitor.is_inside
                    and visitor.entry_time is None
                ),
                "can_check_out": (
                    visitor.status == Visitor.PassStatus.APPROVED
                    and visitor.is_inside
                ),
            }
        })
