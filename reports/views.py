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

        visitors = Visitor.objects.all()

        if from_date and to_date:
            try:
                # from_date_obj = make_aware(datetime.strptime(from_date, "%Y-%m-%d"))
                # to_date_obj = make_aware(datetime.strptime(to_date, "%Y-%m-%d")) + timedelta(days=1)
                # visitors = visitors.filter(created_at__range=(from_date_obj, to_date_obj))
                # from_date_obj = make_aware(datetime.strptime(from_date, "%Y-%m-%d"))
                # # include end of day for to_date
                # to_date_obj = make_aware(datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1))
                from_date_obj = make_aware(datetime.datetime.strptime(from_date, "%Y-%m-%d"))
                to_date_obj = make_aware(datetime.datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1))

                visitors = visitors.filter(created_at__range=(from_date_obj, to_date_obj))
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
                "Mobile": getattr(v, "mobile", ""),
                "Whom to Meet": getattr(v, "whom_to_meet", ""),
                "Visit Date": v.created_at.date() if v.created_at else "",
                "Time In": getattr(v, "time_in", ""),
                "Time Out": getattr(v, "time_out", ""),
                "Duration": getattr(v, "duration", ""),
                "Access Card": getattr(v, "access_card", ""),
                "Category": getattr(v, "category", ""),
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

        if not from_date_str or not to_date_str:
            return HttpResponse("Please provide from_date and to_date", status=400)

        from_date = parse_date(from_date_str)
        to_date = parse_date(to_date_str)

        if not from_date or not to_date:
            return HttpResponse("Invalid date format", status=400)

        visitors = Visitor.objects.filter(visiting_date__range=(from_date, to_date), is_active=True)

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

            data = {
                "visitor_name": row.get("name"),
                "email_id": row.get("email"),
                "mobile_number": str(row.get("phone")),
                "purpose_of_visit": row.get("purpose"),
                "visiting_date": visiting_date
            }

            serializer = BulkVisitorSerializer(data=data, context={'bulk_upload': True})
            if serializer.is_valid():
                serializer.save()
                print(f"✅ Visitor created from row {idx}: {serializer.data}")
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
 
        # Return preview or export
        if export_format == "preview" or request.GET.get("preview") == "true":
            return Response(serialized_data)
 
        filename = f"Monthly_Visitor_Report_{year}_{month:02d}.xlsx"
        return export_to_excel(serialized_data, filename=filename)
    

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
 