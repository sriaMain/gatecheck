from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from .models import OTP
from user_onboarding.models import Company

User = get_user_model()


class CustomLoginSerializer(TokenObtainPairSerializer):
    username_field = 'identifier'

    def get_fields(self):
        fields = super().get_fields()
        fields['identifier'] = serializers.CharField()
        fields['password'] = serializers.CharField(write_only=True)
        fields.pop('username', None)
        fields.pop('email', None)
        return fields



    # def validate(self, attrs):
    #     identifier = attrs.get("identifier")
    #     password = attrs.get("password")

    #     if not identifier or not password:
    #         raise serializers.ValidationError({
    #             "error": "Both identifier and password are required."
    #         })

    #     user = None
    #     field_found = None

    #     # Determine field type
    #     if "@" in identifier:
    #         field = "email"
    #         error_msg = "Email is not registered."
    #     elif identifier.isnumeric():
    #         field = "user_id"
    #         error_msg = "User ID is not registered."
    #     else:
    #         field = "alias_name"
    #         error_msg = "Alias name is not registered."

    #     try:
    #         user = User.objects.get(**{field: identifier})
    #         field_found = field
    #     except User.DoesNotExist:
    #         raise serializers.ValidationError({
    #             "error": error_msg
    #         })

    #     if not user.check_password(password):
    #         raise serializers.ValidationError({
    #             "error": "Incorrect password."
    #         })

    #     if not user.is_active:
    #         raise serializers.ValidationError({
    #             "error": "User account is disabled."
    #         })

    #     refresh = self.get_token(user)

    #     return {
    #         "data": {
    #             "refresh": str(refresh),
    #             "access": str(refresh.access_token),
    #             "user": {
    #                 "id": user.id,
    #                 "user_id": user.user_id,
    #                 "email": user.email,
    #                 "alias_name": user.alias_name,
    #                 "username": user.username,  # Assuming you want to include username
    #                 "company": user.company.company_name if user.company else None,
    #                 "company_id": user.company.id if user.company else None,  # ✅ This is correct
    #                 # "role": user.role.name if user.role else None,
    #                 # "roles": [ur.role.name for ur in user.user_roles.filter(is_active=True)],
    #                 "roles ":user.user_roles.filter(is_active=True).first().role.name \
    #                         if user.user_roles.filter(is_active=True).exists() else None,

                    
                    
    #             }
    #         }
    #     }


    # def get_fields(self):
    #     fields = super().get_fields()
    #     fields['identifier'] = serializers.CharField()
    #     fields['password'] = serializers.CharField(write_only=True)
    #     # remove unwanted fields
    #     fields.pop('username', None)
    #     return fields

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        password = attrs.get("password")

        if not identifier or not password:
            raise serializers.ValidationError({"error": "Both identifier and password are required."})

        user = None

        # 1️⃣ LOGIN USING EMAIL
        if "@" in identifier:
            try:
                user = User.objects.get(email__iexact=identifier)
            except User.DoesNotExist:
                raise serializers.ValidationError({"error": "Email is not registered."})

        # 2️⃣ LOGIN USING USER_ID (ONLY if ALL digits)
        elif identifier.isdigit():
            try:
                user = User.objects.get(user_id=str(identifier))
            except User.DoesNotExist:
                raise serializers.ValidationError({"error": "User ID is not registered."})

        # 3️⃣ LOGIN USING ALIAS NAME
        else:
            try:
                user = User.objects.get(alias_name__iexact=identifier)
            except User.DoesNotExist:
                raise serializers.ValidationError({"error": "Alias name is not registered."})

        # 4️⃣ PASSWORD CHECK
        if not user.check_password(password):
            raise serializers.ValidationError({"error": "Incorrect password."})

        if not user.is_active:
            raise serializers.ValidationError({"error": "User account is disabled."})

        # 5️⃣ GENERATE JWT TOKENS
        refresh = self.get_token(user)

        return {
            "data": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "user_id": user.user_id,
                    "email": user.email,
                    "alias_name": user.alias_name,
                    "username": user.username,
                    "company": user.company.company_name if user.company else None,
                    "company_id": user.company.id if user.company else None,
                    "roles": user.user_roles.filter(is_active=True).first().role.name 
                            if user.user_roles.filter(is_active=True).exists() else None,
                    "is_superuser": user.is_superuser,
                }
            }
        }







class ForgotPasswordSerializer(serializers.Serializer):
    identifier = serializers.CharField()

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        user = None

        for field in ['email', 'user_id']:  # Add/remove fields as per your model
            try:
                user = User.objects.get(**{field: identifier})
                attrs['user'] = user
                return attrs
            except User.DoesNotExist:
                continue

        raise serializers.ValidationError({"error": "User not found."})


class VerifyOTPSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        otp = attrs.get("otp")
        user = None

        for field in ['email', 'user_id']:
            try:
                user = User.objects.get(**{field: identifier})
                break
            except User.DoesNotExist:
                continue

        if not user:
            raise serializers.ValidationError({"identifier": "User not found."})

        otp_obj = OTP.objects.filter(user=user, otp=otp, is_used=False).last()

        if not otp_obj:
            raise serializers.ValidationError({"otp": "Invalid or already used OTP."})
        if not otp_obj.is_valid():
            raise serializers.ValidationError({"otp": "OTP has expired."})

        attrs['otp_obj'] = otp_obj
        return attrs
    




class SetNewPasswordSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        if new_password != confirm_password:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        # Find user by email, user_id, or alias_name
        user = None
        for field in ['email', 'user_id', 'alias_name']:
            try:
                user = User.objects.get(**{field: identifier})
                break
            except User.DoesNotExist:
                continue

        if not user:
            raise serializers.ValidationError({"identifier": "User not found."})

        # Check if there is a verified and not expired OTP for this user
        valid_otp = OTP.objects.filter(
            user=user,
            is_used=True,
            created_at__gte=timezone.now() - timezone.timedelta(minutes=15)
        ).last()

        if not valid_otp:
            raise serializers.ValidationError({"otp": "No verified or valid OTP found. Please verify again."})

        attrs['user'] = user
        return attrs

    def save(self):
        user = self.validated_data['user']
        new_password = self.validated_data['new_password']
        user.password = make_password(new_password)
        user.save()



class ResetPasswordSerializers(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)
  
   
    

    def validate_old_password(self, value):
        user = self.context['request'].user
 
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
 
    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 6 characters long.")
        return value
 
    def save(self, **kwargs):
        """Update user password."""
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()



class ValidateIdentifierSerializer(serializers.Serializer):
    identifier = serializers.CharField(
        error_messages={
            "required": "Identifier (email / user_id / alias_name) is required.",
            "blank": "Identifier cannot be blank."
        }
    )

    def validate_identifier(self, value):
        for field in ['email', 'user_id', 'alias_name']:
            users = User.objects.filter(**{field: value})
            if users.exists():
                if users.count() > 1:
                    raise serializers.ValidationError(
                        f"Multiple users found with this {field}. Please contact support or use a unique identifier."
                    )
                self.context['user'] = users.first()
                return value

        raise serializers.ValidationError("User not found with the given identifier.")



