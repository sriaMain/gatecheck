from django.shortcuts import render
from django.conf import settings
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (CustomLoginSerializer, ForgotPasswordSerializer, VerifyOTPSerializer,
                           SetNewPasswordSerializer, ResetPasswordSerializers, ValidateIdentifierSerializer) 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import OTP
from rest_framework.exceptions import ValidationError
from django.core.mail import send_mail
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import logout
import random

class CustomLoginTokenView(TokenObtainPairView):
    serializer_class = CustomLoginSerializer
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        except ValidationError as exc:
            # Convert error detail to plain string (if needed)
            detail = exc.detail
            if isinstance(detail, (list, dict)):
                if isinstance(detail, dict):
                    detail = next(iter(detail.values()))
                if isinstance(detail, list):
                    detail = detail[0]
            return Response({"error": detail}, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            otp_obj = OTP.objects.create(user=user)

            # Send email
            send_mail(
                subject="Your OTP for Forgot Password",
                message=f"Your OTP is: {otp_obj.otp}. It is valid for 15 minutes.",
                from_email=None,  # Uses DEFAULT_FROM_EMAIL
                recipient_list=[user.email],
                fail_silently=False,
            )

            return Response({"message": "OTP sent successfully to your email."}, status=status.HTTP_200_OK)

        # If serializer is invalid
        detail = serializer.errors
        if isinstance(detail, (list, dict)):
            if isinstance(detail, dict):
                detail = next(iter(detail.values()))
            if isinstance(detail, list):
                detail = detail[0]

        return Response({"error": detail}, status=status.HTTP_400_BAD_REQUEST)

    


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            otp_obj = serializer.validated_data['otp_obj']
            otp_obj.is_used = True
            otp_obj.save()

            return Response({"message": "OTP verified successfully."}, status=status.HTTP_200_OK)

        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class SetNewPasswordView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = SetNewPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password has been set successfully."}, status=status.HTTP_200_OK)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class ResetPasswordView(APIView):
    permission_classess= [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        serializer = ResetPasswordSerializers(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = request.user
            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)
            user.save()
            # return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)
        

            subject = "Your password has been changed successfully"
            message = f"Hello {user.username},\n\nYour password was successfully changed.\nIf you didn't request this change, please contact support immediately."
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [user.email]

            try:
                send_mail(subject, message, from_email, recipient_list)
            except Exception as e:
                    # Optional: Log the error if needed
                print(f"Error sending email: {e}")

            return Response({"message": "Password updated successfully. A confirmation email has been sent."}, status=status.HTTP_200_OK)

        # Get first error message
        detail = serializer.errors
        if isinstance(detail, dict):
            first_key = next(iter(detail))
            first_error = detail[first_key][0] if isinstance(detail[first_key], list) else detail[first_key]
            return Response({"error": str(first_error)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Invalid request."}, status=status.HTTP_400_BAD_REQUEST)
    


class LogoutUserAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def post(self, request):
        logout(request)
        return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
    

class ValidateIdentifierView(APIView):
    permission_classes = [AllowAny] # Allow any user to check


    def post(self, request):
        serializer = ValidateIdentifierSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            return Response({"message": "Identifier is valid."}, status=status.HTTP_200_OK)
        
        # Extract the field error message clearly
        error_message = serializer.errors.get("identifier", ["Unknown error"])[0]
        return Response({"error": error_message}, status=status.HTTP_404_NOT_FOUND)


    
        


