from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.serializers import Serializer
from .models import Company, CustomUser
from roles_creation.models import Role

from .serializers import CustomUserSerializer, CompanySerializer
from roles_creation.permissions import HasRolePermission
from .utils import create_user_and_send_mail



class CompanyAPIView(APIView):
    permission_classes = [IsAuthenticated]  # ✅ Only authenticated users can access
    authentication_classes = [JWTAuthentication]  # ✅ Use JWT for authentication

    def get(self, request, *args, **kwargs):
        """Fetch company details or all companies"""
        self.permission_required = "view_organization"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        company_id = request.query_params.get('id') or kwargs.get('id')
        if company_id:
            try:
                organisation = Company.objects.get(id=company_id)
                serializer = CompanySerializer(organisation)
                return Response(serializer.data)
            except Company.DoesNotExist:
                return Response({"error": "Organisation not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            organisations = Company.objects.all()
            serializer = CompanySerializer(organisations, many=True)
            return Response(serializer.data)
        

    
    def post(self, request):
        serializer = CompanySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    

    def put(self, request, id):
        try:
            organisation = Company.objects.get(id=id)
        except Company.DoesNotExist:
            return Response({"error": "Organisation not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CompanySerializer(organisation, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self, request, id):
        try:
            organisation = Company.objects.get(id=id)
            organisation.delete()
            return Response({"message": "Organisation deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Company.DoesNotExist:
            return Response({"error": "Organisation not found."}, status=status.HTTP_404_NOT_FOUND)
    


    
    


class CreateUserAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]  


    def get(self, request):
        """Fetch user details by user_id or company_id"""
        self.permission_required = "view_users"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        user_id = request.query_params.get('id')
        company_id = request.query_params.get('company_id')
        if user_id:
            try:
                user = CustomUser.objects.get(id=user_id)
                serializer = CustomUserSerializer(user)
                return Response(serializer.data)
            except CustomUser.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


        


        # elif company_id:
        elif company_id and company_id != "undefined":
        # ✅ Check if the company exists
            try:
                company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                return Response({"error": "Organisation not found."}, status=status.HTTP_404_NOT_FOUND)

            # ✅ Fetch users under this company
            users = CustomUser.objects.filter(company_id=company_id)

            if users.exists():
                serializer = CustomUserSerializer(users, many=True)
                return Response(serializer.data)
            else:
                return Response({"message": "No users found for this organisation."}, status=status.HTTP_200_OK)

        else:
            return Response({"error": "Please provide 'company_id' or 'id' as query param."}, status=status.HTTP_400_BAD_REQUEST)

    

    def post(self, request):
        """Create a new user and send credentials via email"""
        self.permission_required = "create_users"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

         # ✅ Use CustomUserSerializer to validate and create user

        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            try:
                validated = serializer.validated_data

                # ✅ role is already a Role instance
                role_instance = validated.get('role', None)

                user = create_user_and_send_mail(
                    email=validated['email'],
                    company=validated['company'],
                    mobile_number=validated.get('mobile_number', ''),
                    alias_name=validated.get('alias_name', ''),
                    block=validated.get('block', ''),
                    floor=validated.get('floor', ''),
                    username=validated.get('username', 'user_' + validated['email'].split('@')[0])
                    # role=role_instance
                )

                return Response({
                    "message": "User created successfully and credentials sent via email.",
                    "user_id": user.user_id,
                    # "role_name": user.role.name if user.role else None,
                    # "role": user.role.id if user.role else None
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    

    def put(self, request, id):
        """Update user details by ID"""
        self.permission_required = "update_users"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            user = CustomUser.objects.get(id=id)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CustomUserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self, request, id):
        try:
            user = CustomUser.objects.get(id=id)
            user.delete()
            return Response({"message": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)






class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        """Fetch user profile details"""
        self.permission_required = "view_profile"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        user = request.user
        company = getattr(user, "company", None)

     

        if hasattr(user, "user_roles"):
            roles = user.user_roles.filter(is_active=True).select_related("role")
            first_role = roles.first()
            role_name = first_role.role.name if first_role and first_role.role else None
        elif hasattr(user, "role"):
            role_name = user.role.name if user.role else None
        else:
            role_name = None

        data = {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "mobile_number": user.mobile_number,
            "alias_name": user.alias_name,
            "block": user.block,
            "floor": user.floor,
            "roles": role_name,   # ✅ updated
            "company": {
                "company_name": company.company_name if company else None,
                "address": company.address if company else None,
                "location": company.location if company else None,
                "pin_code": company.pin_code if company else None,
            } if company else None
        }

        return Response(data)
