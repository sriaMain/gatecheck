from django.urls import path
from .views import (VisitorReportExportView, VisitorPdfExportView, BulkVisitorUploadAPIView,
                    MonthlyVisitorReportExcelView, MonthlyVisitorReportPDFView)


urlpatterns = [
    path('download-visitor-report/', VisitorReportExportView.as_view(), name='download-visitor-report'),
    path('export-pdf/', VisitorPdfExportView.as_view(), name='export-visitor-pdf'),
    path('bulk-upload-visitors/', BulkVisitorUploadAPIView.as_view(), name='bulk-upload-visitors'),
    path('monthly-visitor-excel/', MonthlyVisitorReportExcelView.as_view(), name='monthly-visitor-report'),
    path('monthly-visitor-pdf/', MonthlyVisitorReportPDFView.as_view(), name='monthly-visitor-report-pdf'),
]
