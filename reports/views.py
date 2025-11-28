from django.shortcuts import render


import pandas as pd
from io import BytesIO
from rest_framework.views import APIView
from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from datetime import datetime, timedelta
from add_visitors.models import Visitor
from django.utils.timezone import make_aware
from weasyprint import HTML
# from datetime import timedelta
from django.utils.dateparse import parse_date
from django.template.loader import render_to_string
from django.http import JsonResponse
from calendar import monthrange
from .utils import export_to_excel, generate_pdf_report
from .services import get_visitors_by_date_range
from .serializers import serialize_visitors
from add_visitors.models import VisitorLog
from rest_framework import status
import datetime
# import datetime as dt
from .serializers import BulkVisitorSerializer
from roles_creation.permissions import HasRolePermission

class VisitorReportExportView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        """Export visitor report based on query parameters"""
        self.permission_required = "view_report"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    

        export_format = request.query_params.get("format", "excel").lower().strip()
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")
        date_field = request.query_params.get('date_field', 'created_at')  # 'created_at' or 'visiting_date'

        visitors = Visitor.objects.filter(is_active=True)

        if from_date and to_date:
            try:
                from_date_obj = parse_date(from_date)
                to_date_obj = parse_date(to_date)
                
                if not from_date_obj or not to_date_obj:
                    return HttpResponse("Invalid date format. Use YYYY-MM-DD.", status=400)
                
                # Filter by created_at or visiting_date
                if date_field == 'visiting_date':
                    visitors = visitors.filter(visiting_date__range=(from_date_obj, to_date_obj))
                else:
                    visitors = visitors.filter(created_at__date__range=(from_date_obj, to_date_obj))
            except ValueError:
                return HttpResponse("Invalid date format. Use YYYY-MM-DD.", status=400)

        if not visitors.exists():
            return HttpResponse("No visitor records found.", status=404)

        # Prepare data
        data = []
        for v in visitors:
            data.append({
                "Name": v.visitor_name,
                "Email": v.email_id,
                "Mobile": v.mobile_number,
                "Whom to Meet": v.whom_to_meet,
                "Visit Date": v.visiting_date,
                "Visit Time": v.visiting_time,
                "Entry Time": v.entry_time.strftime("%Y-%m-%d %H:%M") if v.entry_time else "-",
                "Exit Time": v.exit_time.strftime("%Y-%m-%d %H:%M") if v.exit_time else "-",
                "Status": v.status,
                "Pass Type": v.pass_type,
                "Category": str(v.category),
            })
        if export_format == "preview":
            return JsonResponse(data, safe=False)

        # Excel Export
        if export_format == "excel":
            df = pd.DataFrame(data)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name="Visitors")
            output.seek(0)
            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename=visitor_report.xlsx'
            return response
        return HttpResponse("Invalid format. Use 'excel' or 'preview'.", status=400)
        





class VisitorPdfExportView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, *args, **kwargs):
        """Export visitor report as PDF based on query parameters"""
        self.permission_required = "view_pdf"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        from_date_str = request.GET.get('from_date')
        to_date_str = request.GET.get('to_date')
        export_format = request.GET.get('format', 'pdf')  # default to pdf
        preview = request.GET.get('preview', 'false').lower() == 'true'
        date_field = request.GET.get('date_field', 'created_at')  # 'created_at' or 'visiting_date'

        if not from_date_str or not to_date_str:
            return HttpResponse("Please provide from_date and to_date", status=400)

        from_date = parse_date(from_date_str)
        to_date = parse_date(to_date_str)

        if not from_date or not to_date:
            return HttpResponse("Invalid date format", status=400)

        # Filter by created_at (when visitor was added) or visiting_date (scheduled visit)
        if date_field == 'visiting_date':
            visitors = Visitor.objects.filter(visiting_date__range=(from_date, to_date), is_active=True)
        else:
            visitors = Visitor.objects.filter(created_at__date__range=(from_date, to_date), is_active=True)

        if not visitors.exists():
            return HttpResponse("No visitor data found for selected dates", status=404)

        context = {
            'visitors': visitors,
            'from_date': from_date,
            'to_date': to_date,
        }

        if export_format == 'pdf':
            html_string = render_to_string('emails/visitors_weasy_pdf.html', context)
            html = HTML(string=html_string)
            pdf_file = html.write_pdf()

            response = HttpResponse(pdf_file, content_type='application/pdf')

            if preview:
                response['Content-Disposition'] = 'inline; filename="visitor_report.pdf"'
            else:
                response['Content-Disposition'] = f'attachment; filename=visitor_report_{from_date}_{to_date}.pdf'

            return response

        return HttpResponse("Unsupported format", status=400)


from datetime import time
from add_visitors.models import Category
class BulkVisitorUploadAPIView(APIView):
    parser_classes = [MultiPartParser]
    authentication_classes = [JWTAuthentication]  # remove if not using JWT or session auth
    permission_classes = [IsAuthenticated]  # remove if not using JWT or session auth

    def get(self, request):
        return HttpResponse("Use POST method to upload a file.", status=405)
    

    

    def post(self, request):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(file_obj)
        except Exception as e:
            return Response({"error": f"Invalid Excel file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        required_fields = {"name", "email", "phone", "scheduled_date"}
        if not required_fields.issubset(df.columns):
            return Response(
                {"error": f"Missing required fields. Required: {required_fields}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_count = 0
        total_rows = len(df)
        errors = []
        
        # Get default category
        default_category = Category.objects.filter(is_active=True).first()
        if not default_category:
            return Response({"error": "No active category found. Please create a category first."}, status=400)

        for idx, row in enumerate(df.to_dict(orient="records"), start=1):
            print(f"Processing row {idx}: {row}")
            visiting_date_raw = row.get("scheduled_date")
            try:
                visiting_date = pd.to_datetime(visiting_date_raw).date()
            except Exception as e:
                error_msg = f"Row {idx}: Invalid date '{visiting_date_raw}' – Error: {e}"
                print(f"❌ {error_msg}")
                errors.append(error_msg)
                continue

            # Get purpose and ensure it's not empty/null/blank
            purpose = row.get("purpose")
            if not purpose or pd.isna(purpose) or str(purpose).strip() == "":
                purpose = "Bulk Upload - General Visit"
            
            data = {
                "visitor_name": row.get("name"),
                "email_id": row.get("email"),
                "mobile_number": str(row.get("phone")),
                "purpose_of_visit": str(purpose).strip(),
                "visiting_date": visiting_date,
                "visiting_time": time(9, 0),  # Default 9 AM
                "gender": "P",  # Prefer not to say
                "category": default_category.id,
            }

            serializer = BulkVisitorSerializer(data=data, context={'bulk_upload': True})
            if serializer.is_valid():
                visitor = serializer.save()
                
                # Generate OTPs and send email (same as normal visitor creation)
                from add_visitors.models import generate_otp
                from django.contrib.auth.hashers import make_password
                from add_visitors.tasks import send_visit_scheduled_email
                
                entry_otp_plain = generate_otp()
                exit_otp_plain = generate_otp()
                visitor.entry_otp = make_password(entry_otp_plain)
                visitor.exit_otp = make_password(exit_otp_plain)
                visitor.save()
                
                # Send email with OTPs
                try:
                    send_visit_scheduled_email(str(visitor.id), entry_otp_plain, exit_otp_plain)
                except Exception as e:
                    print(f"⚠️ Email failed for row {idx}: {e}")
                
                print(f"✅ Visitor created from row {idx}: {visitor.visitor_name}")
                created_count += 1
            else:
                error_msg = f"Row {idx}: Validation errors – {serializer.errors}"
                print(f"❌ {error_msg}")
                errors.append(error_msg)

        return Response({
            "message": f"{created_count} visitors created out of {total_rows} rows processed.",
            "errors": errors  # include errors for transparency
        }, status=status.HTTP_201_CREATED)
#     from datetime import time
# from add_visitors.models import Category  # adjust import as needed

    # def post(self, request):
    #     file_obj = request.FILES.get("file")
    #     if not file_obj:
    #         return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

    #     try:
    #         df = pd.read_excel(file_obj)
    #     except Exception as e:
    #         return Response({"error": f"Invalid Excel file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    #     required_fields = {"name", "email", "phone", "purpose", "scheduled_date"}
    #     if not required_fields.issubset(df.columns):
    #         return Response(
    #             {"error": f"Missing required fields. Required: {required_fields}"},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     created_count = 0
    #     total_rows = len(df)

    #     # Default values
    #     default_time = time(9, 0)
    #     # default_gender = 'M'  # M/F/O/P
    #     default_category = Category.objects.first()

    #     for row in df.to_dict(orient="records"):
    #         try:
    #             visiting_date_raw = row.get("scheduled_date")
    #             try:
    #                 visiting_date = pd.to_datetime(visiting_date_raw).date()
    #             except Exception as e:
    #                 print(f"❌ Skipping row due to invalid date: {visiting_date_raw} – Error: {e}")
    #                 continue

    #             visitor = Visitor(
    #                 visitor_name=row.get("name"),
    #                 email_id=row.get("email"),
    #                 mobile_number=str(row.get("phone")),
    #                 purpose_of_visit=row.get("purpose"),
    #                 visiting_date=visiting_date,
    #                 visiting_time=default_time,
    #                 # gender=default_gender,
    #                 category=default_category,
    #                 # created_by=request.user,  # Optional but recommended
    #             )
    #             visitor.save()
    #             print("✅ Visitor created:", visitor)
    #             created_count += 1
    #         except Exception as e:
    #             print(f"❌ Skipping row due to save error: {e}")
    #             continue

    #     return Response({
    #         "message": f"{created_count} visitors created out of {total_rows} rows processed."
    #     }, status=status.HTTP_201_CREATED)



class MonthlyVisitorReportExcelView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def get(self, request):
        """Generate monthly visitor report in Excel format"""
        self.permission_required = "view_excel"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        year_str = request.GET.get("year")
        month_str = request.GET.get("month")
        export_format = request.GET.get("format", "excel")  # preview or excel
 
        # Handle invalid inputs
        if not year_str or not month_str or year_str == "undefined" or month_str == "undefined":
            return Response({"error": "Please provide valid year and month."}, status=400)
 
        try:
            year = int(year_str)
            month = int(month_str)
        except ValueError:
            return Response({"error": "Year and month must be integers."}, status=400)
 
        # Query visitors by created_at month
        visitors = Visitor.objects.filter(
            created_at__year=year,
            created_at__month=month,
            is_active=True
        )
        
        if not visitors.exists():
            return Response({"error": "No visitor data found for the selected month."}, status=404)
        
        # Prepare data
        data = []
        for v in visitors:
            data.append({
                "Name": v.visitor_name,
                "Email": v.email_id,
                "Mobile": v.mobile_number,
                "Whom to Meet": v.whom_to_meet,
                "Visit Date": v.visiting_date,
                "Visit Time": v.visiting_time,
                "Entry Time": v.entry_time.strftime("%Y-%m-%d %H:%M") if v.entry_time else "-",
                "Exit Time": v.exit_time.strftime("%Y-%m-%d %H:%M") if v.exit_time else "-",
                "Status": v.status,
                "Pass Type": v.pass_type,
                "Category": str(v.category),
            })
 
        # Return preview or export
        if export_format == "preview" or request.GET.get("preview") == "true":
            return Response(data)
 
        # Excel Export
        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Visitors")
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"Monthly_Visitor_Report_{year}_{month:02d}.xlsx"
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
    

class MonthlyVisitorReportPDFView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
 
    def get(self, request):
        """Generate monthly visitor report in PDF format"""
        self.permission_required = "view_excel"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        year_str = request.GET.get("year")
        month_str = request.GET.get("month")
 
        if not year_str or not month_str or year_str == "undefined" or month_str == "undefined":
            return Response({"error": "Please provide valid year and month."}, status=400)
 
        try:
            year = int(year_str)
            month = int(month_str)
        except ValueError:
            return Response({"error": "Year and month must be integers."}, status=400)
 
        visitors = VisitorLog.objects.filter(
            created_at__year=year,
            created_at__month=month
        )
        if not visitors.exists():
            return Response({"message": "No visitor data found for the selected month."}, status=404)
        data = serialize_visitors(visitors)
        filename = f"Monthly_Visitor_Report_{year}_{month}.pdf"
        return generate_pdf_report(data, filename)
    # def get(self, request):
    #     year_str = request.GET.get("year")
    #     month_str = request.GET.get("month")
    #     preview = request.GET.get("preview", "false").lower() == "true"

    #     # Validate year & month
    #     if not year_str or not month_str or year_str == "undefined" or month_str == "undefined":
    #         return Response({"error": "Please provide valid year and month."}, status=400)
    #     try:
    #         year = int(year_str)
    #         month = int(month_str)
    #     except ValueError:
    #         return Response({"error": "Year and month must be integers."}, status=400)

    #     # Query data
    #     visitors = VisitorLog.objects.filter(
    #         created_at__year=year,
    #         created_at__month=month
    #     ).order_by("created_at")

    #     data = serialize_visitors(visitors)

    #     if not data:
    #         return Response({"error": "No visitors found for this period."}, status=404)

    #     if preview:
    #         # Use HTML template + WeasyPrint
    #         context = {
    #             "from_date": f"{year}-{month:02d}-01",
    #             "to_date": f"{year}-{month:02d}-28",  # You can get real month end if needed
    #             "visitors": data
    #         }
    #         html_string = render_to_string("emails/monthly_pdf.html", context)
    #         pdf_file = HTML(string=html_string).write_pdf()

    #         response = HttpResponse(pdf_file, content_type="application/pdf")
    #         response["Content-Disposition"] = f'inline; filename="Monthly_Visitor_Report_{year}_{month}.pdf"'
    #         return response
    #     else:
    #         # Use ReportLab utils.py function
    #         filename = f"Monthly_Visitor_Report_{year}_{month}.pdf"
    #         return generate_pdf_report(data, filename)
    

class MonthlyVisitorReportExcelView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def get(self, request):
        """Generate monthly visitor report in Excel format"""
        self.permission_required = "view_excel"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        year_str = request.GET.get("year")
        month_str = request.GET.get("month")
        export_format = request.GET.get("format", "excel")  # preview or excel
 
        # Handle invalid inputs
        if not year_str or not month_str or year_str == "undefined" or month_str == "undefined":
            return Response({"error": "Please provide valid year and month."}, status=400)
 
        try:
            year = int(year_str)
            month = int(month_str)
        except ValueError:
            return Response({"error": "Year and month must be integers."}, status=400)
 
        # Compute date range for the month
        from_date = datetime.datetime(year, month, 1)
        to_date = datetime.datetime(year, month, monthrange(year, month)[1])
 
        # Optional filters
        filters = {
            "category": request.GET.get("category"),
            "host_name": request.GET.get("host_name"),
        }
 
        # Get and serialize visitor data
        visitors = get_visitors_by_date_range(from_date, to_date, filters)
        serialized_data = serialize_visitors(visitors)
        print("Serialized Data:", serialized_data)
 
        # Return preview or export
        if export_format == "preview" or request.GET.get("preview") == "true":
            return Response(serialized_data)
 
        filename = f"Monthly_Visitor_Report_{year}_{month:02d}.xlsx"
        return export_to_excel(serialized_data, filename=filename)
 