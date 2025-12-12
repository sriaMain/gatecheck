import logging
from rest_framework.exceptions import NotFound, ValidationError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Role, Permission, RolePermission, UserRole
from .serializers import RoleSerializer, PermissionSerializer, RolePermissionSerializer, UserRoleSerializer
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from roles_creation.permissions import HasRolePermission
from django.core.exceptions import ObjectDoesNotExist
User = get_user_model()
import traceback  # For debugging purposes
from .permissions import HasRolePermission
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.db import transaction
import json
import logging

logger = logging.getLogger(__name__)

class RoleAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request):
        """ Handle GET requests to fetch all roles """
        self.permission_required = "view_roles"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            # self.check_permission(request, "view_roles")
            roles = Role.objects.all()
            if not roles:
                raise NotFound("No roles found.")
            serializer = RoleSerializer(roles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except NotFound as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):

        """ Handle POST requests to create a new role """

        self.permission_required = "create_roles"

        if not HasRolePermission().has_permission(request, self.permission_required):

            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    
        try:

            # Normalize name to avoid case and space issues

            data = request.data.copy()

            data['name'] = data.get('name', '').strip()
    
            serializer = RoleSerializer(data=data)

            if serializer.is_valid():

                serializer.save(created_by=request.user)

                return Response(serializer.data, status=status.HTTP_201_CREATED)
    
            raise ValidationError(serializer.errors)
    
        except ValidationError as e:

            return Response({"error": f"Validation failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        except IntegrityError as e:

            return Response({"error": f"Integrity Error: {str(e)}"}, status=status.HTTP_409_CONFLICT)

        except Exception as e:

            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
class RoleDetailAPIView(APIView):
    permission_classes = [IsAdminUser]
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, pk):
        """ Handle GET requests to fetch a specific role """
        self.permission_required = "view_roles"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            # self.check_permission(request, "view_roles")
            role = get_object_or_404(Role, pk=pk)
            serializer = RoleSerializer(role)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except NotFound as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, role_id):
        """ Handle PUT requests to update an existing role """
        self.permission_required = "update_roles"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            # self.check_permission(request, "update_roles")
            # role = get_object_or_404(Role, pk=role_id)
            # serializer = RoleSerializer(role, data=request.data, partial=True)
            # if serializer.is_valid():
            #     # Check for duplicate roles based on some field
            #     # if Role.objects.filter(name=request.data.get('name')).exclude(pk=role_id).exists():
            #     if Role.objects.filter(name=request.data.get('name')).exclude(pk=role_id).exists():

            #         raise ValidationError("A role with this name already exists.")
            #     serializer.save(modified_by=request.user)
            #     return Response(serializer.data, status=status.HTTP_200_OK)
            role = get_object_or_404(Role, pk=role_id)

            serializer = RoleSerializer(role, data=request.data, partial=True)

            if serializer.is_valid():

                new_name = request.data.get("name", None)

                # ✅ Run duplicate check ONLY if name updated
                if new_name and new_name != role.name:
                    if Role.objects.filter(name=new_name).exists():
                        raise ValidationError({"name": "A role with this name already exists."})

                serializer.save(modified_by=request.user)
                return Response(serializer.data, status=status.HTTP_200_OK)

            raise ValidationError(serializer.errors)
        except ValidationError as e:
            return Response({"error": f"Validation failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            return Response({"error": f"Role not found: {str(e)}"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, role_id):
        """ Handle DELETE requests to remove a role """
        self.permission_required = "delete_roles"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            # self.check_permission(request, "delete_roles")
            role = get_object_or_404(Role, pk=role_id)
            role.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Role.DoesNotExist:
            return Response({"error": "Role not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PermissionAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]    

    
    def get(self, request):
        """ Handle GET requests to fetch all permissions """
        self.permission_required = "view_roles"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            permissions = Permission.objects.all()
            print("Permissions Count:", permissions.count())  # 👈 debug
            if not permissions.exists():  # ✅ Proper way to check if QuerySet is empty
                raise NotFound("No permissions found.")
            serializer = PermissionSerializer(permissions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except NotFound as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
            



    # @admin_required
    def post(self, request):
        """ Handle POST requests to create a new permission """
        self.permission_required = "create_roles"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            serializer = PermissionSerializer(data=request.data)
            if serializer.is_valid():
                # Check for duplicate permissions based on the name
                if Permission.objects.filter(name=request.data.get('name')).exists():
                    raise ValidationError("A permission with this name already exists.")
                serializer.save(created_by=request.user, modified_by=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            raise ValidationError(serializer.errors)
        except ValidationError as e:
            return Response({"error": f"Validation failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"error": f"Integrity Error: {str(e)}"}, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # @admin_required
    def put(self, request, permission_id):
        """ Handle PUT requests to update an existing permission """
        self.permission_required = "update_roles"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            permission = get_object_or_404(Permission, pk=permission_id)
            serializer = PermissionSerializer(permission, data=request.data, partial=True)
            if serializer.is_valid():
                # Check for duplicate permissions based on name
                if Permission.objects.filter(name=request.data.get('name')).exclude(pk=permission_id).exists():
                    raise ValidationError("A permission with this name already exists.")
                serializer.save(modified_by=request.user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            raise ValidationError(serializer.errors)
        except ValidationError as e:
            return Response({"error": f"Validation failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Permission.DoesNotExist:
            return Response({"error": "Permission not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    # @admin_required
    def delete(self, request, permission_id):
        """ Handle DELETE requests to remove a permission """
        self.permission_required = "delete_roles"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            permission = get_object_or_404(Permission, pk=permission_id)
            permission.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Permission.DoesNotExist:
            return Response({"error": "Permission not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
class RolePermissionAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]    

    
    def get(self, request, role_permission_id=None):
        self.permission_required = "view_roles"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            if role_permission_id:
                role_permission = get_object_or_404(RolePermission, pk=role_permission_id)
                serializer = RolePermissionSerializer(role_permission)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                role_permissions = RolePermission.objects.all()
                if not role_permissions:
                    raise NotFound("No role-permission associations found.")
                serializer = RolePermissionSerializer(role_permissions, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
        except NotFound as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def post(self, request, *args, **kwargs):
        self.permission_required = "create_roles"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = RolePermissionSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   
    def put(self, request, role_id):
        """
        Update role permissions and/or is_active status.
        - Send {"permission": [1,2,3]} to update permissions
        - Send {"is_active": false} to deactivate
        - Send both to update permissions AND status
        """
        self.permission_required = "update_roles"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=403)

        # ---- Fetch Role ----
        role_obj = Role.objects.filter(role_id=role_id).first()
        if not role_obj:
            return Response({"error": "Role not found"}, status=404)

        try:
            with transaction.atomic():
                # Fetch or create RolePermission link
                role_perm_link, created = RolePermission.objects.get_or_create(role=role_obj)
                updated_fields = []

                # ----------------------------------------
                # 1) Update is_active
                # ----------------------------------------
                if 'is_active' in request.data:
                    is_active = request.data.get('is_active')
                    if isinstance(is_active, bool):
                        role_perm_link.is_active = is_active
                    else:
                        # accept "true","false","1","0"
                        role_perm_link.is_active = str(is_active).lower() in ['true', '1']
                    updated_fields.append("is_active")

                # ----------------------------------------
                # 2) Update permissions
                # ----------------------------------------
                raw = request.data.get("permission")
                if raw is not None:
                    # Normalize input into a list
                    if isinstance(raw, list):
                        perms_input = raw
                    elif isinstance(raw, str):
                        try:
                            parsed = json.loads(raw)
                            perms_input = parsed if isinstance(parsed, list) else [parsed]
                        except Exception:
                            perms_input = [p.strip() for p in raw.split(",") if p.strip()]
                    else:
                        perms_input = [raw]

                    resolved = []   # Permission instances
                    invalid = []

                    for p in perms_input:
                        perm_obj = None
                        # 1) numeric id
                        if str(p).isdigit():
                            perm_obj = Permission.objects.filter(permission_id=int(p)).first()
                        # 2) try codename if exists
                        if not perm_obj:
                            # try lookup by 'codename' if model has it; otherwise skip
                            if hasattr(Permission, '_meta') and any(f.name == 'codename' for f in Permission._meta.get_fields()):
                                perm_obj = Permission.objects.filter(codename=str(p)).first()
                        # 3) try lookup by name (case-insensitive)
                        if not perm_obj:
                            perm_obj = Permission.objects.filter(name__iexact=str(p)).first()

                        if perm_obj:
                            resolved.append(perm_obj)
                        else:
                            invalid.append(p)

                    if invalid:
                        return Response({"error": "Invalid permissions", "invalid": invalid}, status=400)

                    # compute add/remove sets
                    current_ids = set(role_perm_link.permission.values_list("permission_id", flat=True))
                    new_ids = set([int(p.permission_id) for p in resolved])

                    # Add missing
                    to_add = new_ids - current_ids
                    if to_add:
                        role_perm_link.permission.add(*Permission.objects.filter(permission_id__in=to_add))
                        updated_fields.append("permissions")

                    # Remove unchecked
                    to_remove = current_ids - new_ids
                    if to_remove:
                        role_perm_link.permission.remove(*Permission.objects.filter(permission_id__in=to_remove))
                        updated_fields.append("permissions")

                # ----------------------------------------
                # 3) Save & respond
                # ----------------------------------------
                if updated_fields:
                    role_perm_link.save()

                    # return permission list using fields that actually exist on Permission
                    # prefer permission_id and name (fall back if name absent)
                    perm_values = []
                    perms_qs = role_perm_link.permission.all()
                    if perms_qs.exists():
                        # choose fields to return based on model fields
                        if any(f.name == 'name' for f in Permission._meta.get_fields()):
                            perm_values = list(perms_qs.values("permission_id", "name"))
                        elif any(f.name == 'codename' for f in Permission._meta.get_fields()):
                            perm_values = list(perms_qs.values("permission_id", "codename"))
                        else:
                            # fallback: just return IDs
                            perm_values = list(perms_qs.values("permission_id"))

                    return Response({
                        "message": f"Updated: {', '.join(dict.fromkeys(updated_fields))}",
                        "is_active": role_perm_link.is_active,
                        "permissions_count": role_perm_link.permission.count(),
                        "permissions": perm_values
                    }, status=200)

                return Response({"message": "No changes made"}, status=200)

        except IntegrityError as e:
            logger.exception("DB integrity error: %s", e)
            return Response({"error": "DB integrity error"}, status=400)
        except Exception as e:
            logger.exception("Unexpected error: %s", e)
            return Response({"error": str(e)}, status=500)
    
    

    

    
        



        
    def delete(self, request, role_permission_id):
            """ Handle DELETE requests to remove a role-permission association """
            self.permission_required = "dlete_roles"
            if not HasRolePermission().has_permission(request, self.permission_required):
                return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
            try:
                # self.check_permission(request, "remove_permissions_from_roles")
                role_permission = get_object_or_404(RolePermission, pk=role_permission_id)
                role_permission.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except RolePermission.DoesNotExist:
                return Response({"error": "Role-Permission association not found."}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserRoleAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def check_permission(self, request, permission_required):
        """ Check if the user has the required permission """
        if not HasRolePermission().has_permission(request, permission_required):
            return Response({'error': 'Permission denied.'}, status=403)

    def get(self, request):     
        """ Handle GET requests to fetch all user-role associations, with optional company_id filtering """
        self.permission_required = "view_roles"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            company_id = request.query_params.get('company_id')
            # If not superuser, only allow access to their own company
            if not request.user.is_superuser:
                user_company_id = getattr(getattr(request.user, 'company', None), 'id', None)
                if company_id and str(company_id) != str(user_company_id):
                    return Response({'error': 'Permission denied: You cannot view roles for another company.'}, status=status.HTTP_403_FORBIDDEN)
                if user_company_id:
                    user_roles = UserRole.objects.filter(user__company_id=user_company_id)
                else:
                    user_roles = UserRole.objects.none()
            elif company_id:
                user_roles = UserRole.objects.filter(user__company_id=company_id)
            else:
                user_roles = UserRole.objects.all()
            if not user_roles:
                raise NotFound("No user-role associations found.")
            serializer = UserRoleSerializer(user_roles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except NotFound as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

  

    def post(self, request):
        """Assign a role to a user."""
        self.permission_required = "create_roles"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            # ✅ Expecting: {"user": 1, "role": 2}
            serializer = UserRoleSerializer(data=request.data)
            if serializer.is_valid():
                # ✅ Check for duplicate
                if UserRole.objects.filter(user=request.data['user'], role=request.data['role']).exists():
                    return Response({'error': 'This role is already assigned to the user.'}, status=status.HTTP_400_BAD_REQUEST)

                serializer.save(created_by = request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_users_without_roles(self, request):
        """Return users who do NOT have any active roles assigned."""
        self.permission_required = "view_roles"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            users_with_roles = UserRole.objects.filter(is_active=True).values_list('user_id', flat=True)
            users_without_roles = User.objects.exclude(id__in=users_with_roles)
            # You can customize fields as needed
            data = list(users_without_roles.values('id', 'username', 'email'))
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class UserRoleDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]  
    authentication_classes = [JWTAuthentication]

    def put(self, request, user_role_id):
        """ Handle PUT requests to update a user-role association """
        self.permission_required = "update_roles"
        if not HasRolePermission().has_permission(request, self.permission_required):   
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            user_role = get_object_or_404(UserRole, pk=user_role_id)
            serializer = UserRoleSerializer(user_role, data=request.data, partial=True)

            if serializer.is_valid():
                user = request.data.get('user', user_role.user_id)
                role = request.data.get('role', user_role.role_id)

                if not user or not role:
                    raise ValidationError("User and role fields are required.")

                # Prevent duplicate assignment
                if UserRole.objects.filter(user=user, role=role).exclude(pk=user_role_id).exists():
                    raise ValidationError("This role is already assigned to the user.")

                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            raise ValidationError(serializer.errors)

        except ValidationError as e:
            return Response({"error": f"Validation failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(traceback.format_exc())  # For debugging only
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # def put(self, request, user_role_id):

    #     self.permission_required = "update_roles"
    #     if not HasRolePermission().has_permission(request, self.permission_required):
    #         return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    #     user_role = get_object_or_404(UserRole, pk=user_role_id)

    #     serializer = UserRoleSerializer(user_role, data=request.data, partial=True)

    #     if serializer.is_valid():
    #         # Use existing values when not provided
    #         user = request.data.get('user', user_role.user_id)
    #         role = request.data.get('role', user_role.role_id)

    #         # Check duplicate only
    #         if UserRole.objects.filter(user=user, role=role).exclude(pk=user_role_id).exists():
    #             raise ValidationError("This role is already assigned to the user.")

    #         serializer.save(modified_by = request.user)
    #         return Response(serializer.data, status=status.HTTP_200_OK)

    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




   
    def get(self, request, user_role_id):
        """ Handle GET requests to fetch a specific user-role association """
        self.permission_required = "view_roles"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            # self.check_permission(request, "view_roles")
            user_role = get_object_or_404(UserRole, pk=user_role_id)
            serializer = UserRoleSerializer(user_role)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserRole.DoesNotExist:
            return Response({"error": "User-Role association not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def delete(self, request, user_role_id):
        """ Handle DELETE requests to remove a user-role association """
        self.permission_required = "delete_roles"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            # self.check_permission(request, "remove_roles_from_users")
            user_role = get_object_or_404(UserRole, pk=user_role_id)
            user_role.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserRole.DoesNotExist:
            return Response({"error": "User-Role association not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)