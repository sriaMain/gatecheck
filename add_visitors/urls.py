
from django.urls import path


from .views import (DashboardAPIView, VisitorDashboardStatusAPIView, VisitorListAPIView, VisitorDetailAPIView, VisitorApprovalAPIView, 
                    VisitorEntryExitView,CategoryListAPIView, VisitorRescheduleAPIView,VisitorProgressAPIView,
                    VehicleListAPIView, VisitorApprovalDecisionView, VisitorFilterAPIView, CompanyVisitorsAPIView, 
                    VerifyVisitorEntryOTPView, QRCodeScanAPIView, VerifyVisitorOTPAPIView, VisitorDashboardStatusAPIView)

urlpatterns = [
    # Dashboard,
    path('dashboard/', DashboardAPIView.as_view(), name='dashboard'),
    
    # Visitors
    path('visitors/', VisitorListAPIView.as_view(), name='visitor-list'),
    path('filter/', VisitorFilterAPIView.as_view(), name='visitor-filter'),
    path('visitors/<uuid:pk>/', VisitorDetailAPIView.as_view(), name='visitor-detail'),
    path('visitor/<uuid:pk>/qr-code/', VisitorListAPIView.as_view(), name='visitor-qr-code'),
    path('visitors/<uuid:pk>/approval/', VisitorApprovalAPIView.as_view(), name='visitor-approval'),
    path('visitors/<uuid:pk>/reject/', VisitorApprovalAPIView.as_view(), name='visitor-reject'),
    path('visitor/decision/<uuid:pk>/', VisitorApprovalDecisionView.as_view(), name='visitor-decision'),
    path('visitors/<str:pass_id>/entry-exit/', VisitorEntryExitView.as_view(), name='visitor-entry-exit'),
    path('visitors/<uuid:pk>/reschedule/', VisitorRescheduleAPIView.as_view(), name='visitor-reschedule'),
    path('company/<int:company_id>/visitors/', CompanyVisitorsAPIView.as_view(), name='company-visitors'),
    path('verify-entry-otp/', VerifyVisitorEntryOTPView.as_view(), name='verify-entry-otp'),
    path('qr-scan/', QRCodeScanAPIView.as_view(), name='qr-scan'),
    path('otp/', VerifyVisitorOTPAPIView.as_view(), name='verify-otp'),
    path('visitors-status/', VisitorDashboardStatusAPIView.as_view(), name='visitors-status'),
    path('progress/<str:pass_id>/', VisitorProgressAPIView.as_view(), name='dashboard-status'),

    
    # Master Data
    # path('companies/', CompanyListAPIView.as_view(), name='company-list'),
    path('categories/', CategoryListAPIView.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryListAPIView.as_view(), name='category-detail'),
    path('vehicles/', VehicleListAPIView.as_view(), name='vehicle-list'),
    path('vehicles/<uuid:uuid>/', VehicleListAPIView.as_view(), name='vehicle-detail'),
]
# from django.urls import path
# from .views import (
#     DashboardAPIView,
#     VisitorListAPIView,
#     VisitorDetailAPIView,
#     VisitorApprovalAPIView,
#     VisitorEntryExitView,
#     CategoryListAPIView,
#     VisitorRescheduleAPIView,
#     VehicleListAPIView,
#     VisitorApprovalDecisionView,
#     VisitorFilterAPIView,
#     CompanyVisitorsAPIView,
#     VerifyVisitorEntryOTPView,
#     QRCodeScanAPIView
# )

# urlpatterns = [
#     # Dashboard
#     path('dashboard/', DashboardAPIView.as_view()),

#     # Visitors
#     path('', VisitorListAPIView.as_view(), name='visitor-list'),
#     path('filter/', VisitorFilterAPIView.as_view()),
#     path('<uuid:pk>/', VisitorDetailAPIView.as_view()),
#     path('<uuid:pk>/approval/', VisitorApprovalAPIView.as_view()),
#     path('<uuid:pk>/reject/', VisitorApprovalAPIView.as_view()),
#     path('decision/<uuid:pk>/', VisitorApprovalDecisionView.as_view()),
#     path('<str:pass_id>/entry-exit/', VisitorEntryExitView.as_view()),
#     path('<uuid:pk>/reschedule/', VisitorRescheduleAPIView.as_view()),
#     path('company/<int:company_id>/', CompanyVisitorsAPIView.as_view()),
#     path('verify-entry-otp/', VerifyVisitorEntryOTPView.as_view()),

#     # ✅ QR Scan (THIS IS THE IMPORTANT ONE)
#     path('qr-scan/', QRCodeScanAPIView.as_view(), name='qr-scan'),

#     # Master Data
#     path('categories/', CategoryListAPIView.as_view()),
#     path('categories/<int:pk>/', CategoryListAPIView.as_view()),
#     path('vehicles/', VehicleListAPIView.as_view()),
#     path('vehicles/<uuid:uuid>/', VehicleListAPIView.as_view()),
# ]
