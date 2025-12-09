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

    # def post(self, request):

    
    #     self.permission_required = "create_visitor"
    #     if not HasRolePermission().has_permission(request, self.permission_required):
    #         return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    #     serializer = VisitorCreateUpdateSerializer(data=request.data)
    #     if serializer.is_valid():
    #         try:
    #             with transaction.atomic():
    #                 visitor = serializer.save(created_by=request.user)

    #                 # ✅ Generate Plain OTPs
    #                 entry_otp_plain = generate_otp()
    #                 exit_otp_plain = generate_otp()

    #                 # ✅ Hash OTPs before saving
    #                 visitor.entry_otp = make_password(entry_otp_plain)
    #                 visitor.exit_otp = make_password(exit_otp_plain)
    #                 visitor.save()

    #                 logger.info(f"Visitor saved with ID: {visitor.id}")
    #                 QRCodeService().generate_visitor_qr(visitor)

    #                 # ✅ Send Email with plain OTPs
    #                 transaction.on_commit(lambda: send_visit_scheduled_email.apply_async(
    #                     args=[str(visitor.id), entry_otp_plain, exit_otp_plain],
    #                     countdown=2
    #                 ))

    #                 # response_data = VisitorDetailSerializer(visitor).data
    #                 response_data = VisitorDetailSerializer(visitor, context={'request': request}).data
    #                 response_data['message'] = 'Visitor created successfully'
    #                 response_data['email_status'] = "Visit scheduled email task triggered"
    #                 return Response(response_data, status=status.HTTP_201_CREATED)

    #         except Exception as e:
    #             logger.error(f"Error creating visitor: {str(e)}")
    #             return Response(
    #                 {'error': 'Failed to create visitor. Please try again.'},
    #                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #             )

    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # from datetime import date

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



# class VisitorEntryExitAPIView(BaseAPIView):
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [JWTAuthentication] 
#     """API view for managing visitor entry and exit"""
    

    # def post(self, request, pk):
    #     self.permission_required = "create_entry"
    #     if not HasRolePermission().has_permission(request, self.permission_required):
    #         return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    #     """Record visitor entry or exit"""
    #     visitor = get_object_or_404(Visitor, pk=pk, is_active=True)
    #     action = request.data.get('action')  # 'entry' or 'exit'
    #     notes = request.data.get('notes', '')

    #     if action not in ['entry', 'exit']:
    #         return Response(
    #             {'error': 'Action must be either "entry" or "exit"'},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     if visitor.status != 'APPROVED':
    #         return Response(
    #             {'error': 'Only approved visitors can enter/exit'},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     # 🛑 Check if pass is expired
    #     if date.today() > visitor.visiting_date:
    #         return Response(
    #             {'error': 'Visitor pass has expired.'},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     # ✅ Visiting date must be today
    #     if visitor.visiting_date != date.today():
    #         return Response(
    #             {'error': 'Visitor is not scheduled for today.'},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     if action == 'entry':
    #         if visitor.is_inside:
    #             return Response(
    #                 {'error': 'Visitor is already inside'},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )
    #     elif action == 'exit':
    #         if not visitor.is_inside:
    #             return Response(
    #                 {'error': 'Visitor is not inside'},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )

    #     now = timezone.now()
    #     if action == 'entry':
    #         visitor.entry_time = now
    #         visitor.is_inside = True
    #     else:
    #         visitor.exit_time = now
    #         visitor.is_inside = False

    #     visitor.save()

    #     # Log the action
    #     VisitorLog.objects.create(
    #         visitor=visitor,
    #         action=action.upper(),
    #         security_guard=request.user,
    #         notes=notes
    #     )

    #     serializer = VisitorDetailSerializer(visitor)
    #     return Response(serializer.data)
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from django.shortcuts import get_object_or_404
# from django.utils import timezone
# from django.contrib.auth.hashers import check_password
# from .models import Visitor, VisitorLog
# from .serializers import VisitorDetailSerializer

# class VisitorEntryExitView(APIView):
#     """
#     API to handle visitor check-in (entry) and check-out (exit) with OTP verification.
#     """
#     permission_classes = []  # Add your auth if needed

#     def post(self, request, pass_id):
#         # Fetch visitor by pass_id
#         visitor = get_object_or_404(Visitor, pass_id=pass_id, is_active=True)

#         action = request.data.get('action')   # 'entry' or 'exit'
#         otp = request.data.get('otp')         # OTP entered by visitor
#         notes = request.data.get('notes', '')

#         # Validate action
#         if action not in ['entry', 'exit']:
#             return Response({'error': 'Action must be either "entry" or "exit"'}, status=status.HTTP_400_BAD_REQUEST)

#         # Only approved visitors
#         if visitor.status != Visitor.PassStatus.APPROVED:
#             return Response({'error': 'Only approved visitors can enter/exit'}, status=status.HTTP_400_BAD_REQUEST)

#         # Check visiting date
#         today = timezone.localdate()
#         if visitor.visiting_date != today:
#             return Response({'error': 'Visitor is not scheduled for today.'}, status=status.HTTP_400_BAD_REQUEST)

#         # OTP Verification
#         if action == 'entry':
#             if not visitor.entry_otp:
#                 return Response({'error': 'Entry OTP not generated yet.'}, status=status.HTTP_400_BAD_REQUEST)
#             if not check_password(otp, visitor.entry_otp):
#                 return Response({'error': 'Invalid entry OTP'}, status=status.HTTP_400_BAD_REQUEST)
#             if visitor.is_inside:
#                 return Response({'error': 'Visitor is already inside.'}, status=status.HTTP_400_BAD_REQUEST)
#             visitor.entry_time = timezone.now()
#             visitor.is_inside = True

#         elif action == 'exit':
#             if not visitor.exit_otp:
#                 return Response({'error': 'Exit OTP not generated yet.'}, status=status.HTTP_400_BAD_REQUEST)
#             if not check_password(otp, visitor.exit_otp):
#                 return Response({'error': 'Invalid exit OTP'}, status=status.HTTP_400_BAD_REQUEST)
#             if not visitor.is_inside:
#                 return Response({'error': 'Visitor is not inside.'}, status=status.HTTP_400_BAD_REQUEST)
#             visitor.exit_time = timezone.now()
#             visitor.is_inside = False

#         # Save visitor status
#         visitor.save()

#         # Log the action
#         VisitorLog.objects.create(
#             visitor=visitor,
#             action=action.upper(),
#             security_guard=request.user if request.user.is_authenticated else None,
#             notes=notes
#         )

#         serializer = VisitorDetailSerializer(visitor)
#         return Response(serializer.data, status=status.HTTP_200_OK)


# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from django.shortcuts import get_object_or_404
# from django.utils import timezone
# from django.contrib.auth.hashers import check_password
# from .models import Visitor, VisitorLog
# from .serializers import VisitorDetailSerializer
# import pytz

# class VisitorEntryExitView(APIView):
#     """
#     API to handle visitor check-in (entry) and check-out (exit) with OTP verification.
#     OTP is invalidated after successful use to prevent reuse.
#     """
#     permission_classes = []  # Add your auth if needed

#     def post(self, request, pass_id):
#         # Get visitor
#         visitor = get_object_or_404(Visitor, pass_id=pass_id, is_active=True)

#         action = request.data.get('action')   # 'entry' or 'exit'
#         otp = request.data.get('otp')         # OTP entered by visitor
#         notes = request.data.get('notes', '')

#         # Validate action
#         if action not in ['entry', 'exit']:
#             return Response({'error': 'Action must be either "entry" or "exit"'}, status=status.HTTP_400_BAD_REQUEST)

#         # Only approved visitors
#         if visitor.status != Visitor.PassStatus.APPROVED:
#             return Response({'error': 'Only approved visitors can enter/exit'}, status=status.HTTP_400_BAD_REQUEST)
#         ist = pytz.timezone('Asia/Kolkata')
#         scheduled_naive = datetime.combine(visitor.visiting_date, visitor.visiting_time)
#         scheduled_ist = ist.localize(scheduled_naive)  # Scheduled visiting time in IST
#         now_ist = timezone.now().astimezone(ist)       # Current time in IST

#         if action == 'entry':
#             if visitor.is_inside:
#                 return Response({'error': 'Visitor has already checked in.'}, status=status.HTTP_400_BAD_REQUEST)

#             # Prevent early check-in
#             if now_ist < scheduled_ist:
#                 return Response({'error': 'Visitor cannot check in before the scheduled visiting time.'},
#                                 status=status.HTTP_400_BAD_REQUEST)
      
#         if action == 'entry':
#             if visitor.is_inside:
#                 return Response({'error': 'Visitor has already checked in.'}, status=status.HTTP_400_BAD_REQUEST)

#             # Prevent early check-in
#             scheduled_datetime = datetime.combine(visitor.visiting_date, visitor.visiting_time)
#             if timezone.now() < timezone.make_aware(scheduled_datetime):
#                 return Response({'error': 'Visitor cannot check in before the scheduled visiting time.'},
#                                 status=status.HTTP_400_BAD_REQUEST)

#             if not visitor.entry_otp:
#                 return Response({'error': 'Entry OTP not generated or already used.'}, status=status.HTTP_400_BAD_REQUEST)
#             if not check_password(otp, visitor.entry_otp):
#                 return Response({'error': 'Invalid entry OTP'}, status=status.HTTP_400_BAD_REQUEST)

#             # Record entry
#             visitor.entry_time = timezone.now()
#             visitor.is_inside = True
#             visitor.entry_otp = None  # OTP invalidated

#         elif action == 'exit':
#             if not visitor.is_inside:
#                 return Response({'error': 'Visitor has not checked in yet or already checked out.'}, status=status.HTTP_400_BAD_REQUEST)
#             if not visitor.exit_otp:
#                 return Response({'error': 'Exit OTP not generated or already used.'}, status=status.HTTP_400_BAD_REQUEST)
#             if not check_password(otp, visitor.exit_otp):
#                 return Response({'error': 'Invalid exit OTP'}, status=status.HTTP_400_BAD_REQUEST)

#             # Record exit
#             visitor.exit_time = timezone.now()
#             visitor.is_inside = False
#             visitor.exit_otp = None  # OTP invalidated


#         # Save visitor
#         visitor.save()

#         # Log action
#         VisitorLog.objects.create(
#             visitor=visitor,
#             action=action.upper(),
#             security_guard=request.user if request.user.is_authenticated else None,
#             notes=notes
#         )

#         serializer = VisitorDetailSerializer(visitor)
#         return Response(serializer.data, status=status.HTTP_200_OK)



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



class QRCodeScanAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        """Handle QR code scan for visitor entry/exit"""
        self.permission_required = "create_qr"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        pass_id = request.data.get('pass_id')
        try:
            visitor = Visitor.objects.get(pass_id=pass_id, is_active=True)
        except Visitor.DoesNotExist:
            return Response({'error': 'Invalid QR or pass ID'}, status=404)

        if not visitor.is_inside:
            visitor.entry_time = timezone.now()
            visitor.is_inside = True
        else:
            visitor.exit_time = timezone.now()
            visitor.is_inside = False
        visitor.save()
        return Response({'message': 'Status updated', 'status': 'Inside' if visitor.is_inside else 'Exited'})


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

        # Check OTP match
        if visitor.entry_otp != otp:
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

        # Return visitor details
        return Response({
            "message": "Visitor checked in successfully",
            "visitor": {
                "pass_id": visitor.pass_id,
                "visitor_name": visitor.visitor_name,
                "mobile_number": visitor.mobile_number,
                "email_id": visitor.email_id,
                "gender": visitor.gender,
                "whom_to_meet": visitor.whom_to_meet,
                "purpose_of_visit": visitor.purpose_of_visit,
                "visiting_date": visitor.visiting_date,
                "visiting_time": visitor.visiting_time,
                "is_inside": visitor.is_inside,
            }
        }, status=status.HTTP_200_OK)
1
