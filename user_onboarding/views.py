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
                # Check if user is superuser or belongs to this company
                if not request.user.is_superuser and getattr(request.user, 'company_id', None) != organisation.id:
                    return Response({"error": "You do not have access to view this organization."}, status=status.HTTP_403_FORBIDDEN)
                serializer = CompanySerializer(organisation)
                return Response(serializer.data)
            except Company.DoesNotExist:
                return Response({"error": "Organisation not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Superusers see all companies; others see only their own
            if request.user.is_superuser:
                organisations = Company.objects.all()
            elif request.user.company:
                organisations = Company.objects.filter(id=request.user.company.id)
            else:
                # If user has no company, return an empty list
                organisations = Company.objects.none()
                
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


    def get(self, request, id=None):
        """Fetch user details by user_id, company_id, or all users for superadmin."""
        self.permission_required = "view_users"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        # Accept id from URL or query param
        user_id = id if id is not None else request.query_params.get('id')
        company_id = request.query_params.get('company_id')

        # Fetch by user_id
        if user_id:
            try:
                user = CustomUser.objects.get(id=user_id)
                serializer = CustomUserSerializer(user)
                return Response(serializer.data)
            except CustomUser.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


        # Company-wise filtering (applies to all, including superuser)
        if company_id and company_id != "undefined":
            try:
                company_id_int = int(company_id)
            except (TypeError, ValueError):
                return Response({"error": "Invalid company_id."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                company = Company.objects.get(id=company_id_int)
            except Company.DoesNotExist:
                return Response({"error": "Organisation not found."}, status=status.HTTP_404_NOT_FOUND)
            # Debug: print all users and their company assignments
            all_users = CustomUser.objects.all()
            print("All users and their company assignments:")
            for u in all_users:
                print(f"User ID: {u.id}, Username: {u.username}, Company ID: {getattr(u, 'company_id', None)}")
            users = CustomUser.objects.filter(company_id=company_id_int)
            print("Filtering users for company_id:", company_id_int)
            print("Queryset:", users.query)
            serializer = CustomUserSerializer(users, many=True)
            return Response(serializer.data)

        # Superadmin: return all users only if no company_id filter
        if hasattr(request.user, 'is_superuser') and request.user.is_superuser:
            users = CustomUser.objects.all()
            serializer = CustomUserSerializer(users, many=True)
            return Response(serializer.data)

        # Default: return users for current user's company
        if hasattr(request.user, 'company') and request.user.company:
            users = CustomUser.objects.filter(company_id=request.user.company.id)
            serializer = CustomUserSerializer(users, many=True)
            return Response(serializer.data)

        return Response({"error": "No users found or insufficient parameters."}, status=status.HTTP_400_BAD_REQUEST)
    

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
