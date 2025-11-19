
from django.urls import path
from .views import (CustomLoginTokenView, ForgotPasswordView, VerifyOTPView, 
                    SetNewPasswordView, ResetPasswordView, LogoutUserAPIView, ValidateIdentifierView)

urlpatterns = [
    path('login/', CustomLoginTokenView.as_view(), name='custom-login'),
    path('otp-request/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('set-new-password/', SetNewPasswordView.as_view(), name='set-new-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('logout/', LogoutUserAPIView.as_view(), name='logout-user'),
    path('validate/', ValidateIdentifierView.as_view(), name='validate-identifier'),
]
