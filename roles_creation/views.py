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
   
    
    

    # def put(self, request, role_id):
    #     """
    #     Assign permissions to a role.
    #     - Accepts: list of permission_ids or codenames.
    #     - Adds only new ones (does not remove existing).
    #     - Returns what was newly assigned vs already existing.
    #     """
    #     self.permission_required = "update_roles"
    #     if not HasRolePermission().has_permission(request, self.permission_required):
    #         return Response({'error': 'Permission denied.'}, status=403)

    #     raw = request.data.get("permission")
    #     if raw is None:
    #         return Response({"error": "permission field is required"}, status=400)

    #     # ✅ Normalize input
    #     if isinstance(raw, list):
    #         perms_input = raw
    #     elif isinstance(raw, str):
    #         try:
    #             parsed = json.loads(raw)
    #             perms_input = parsed if isinstance(parsed, list) else [parsed]
    #         except Exception:
    #             perms_input = [p.strip() for p in raw.split(",") if p.strip()]
    #     else:
    #         perms_input = [raw]

    #     # ✅ Check role
    #     role_obj = Role.objects.filter(role_id=role_id).first()
    #     if not role_obj:
    #         return Response({"error": "Role not found."}, status=404)

    #     # ✅ Models
    #     from roles_creation.models import Permission as RolePermModel
    #     from django.contrib.auth.models import Permission as AuthPermission

    #     resolved_objs = []
    #     invalid = []

    #     # ✅ Resolve IDs / codenames
    #     for p in perms_input:
    #         if isinstance(p, int) or (isinstance(p, str) and p.isdigit()):
    #             pid = int(p)
    #             perm_obj = RolePermModel.objects.filter(permission_id=pid).first()
    #             if perm_obj:
    #                 resolved_objs.append(perm_obj)
    #                 continue
    #             # fallback to Django auth_permission mapping
    #             auth_perm = AuthPermission.objects.filter(id=pid).first()
    #             if auth_perm:
    #                 mapped = RolePermModel.objects.filter(codename=auth_perm.codename).first()
    #                 if mapped:
    #                     resolved_objs.append(mapped)
    #                     continue
    #             invalid.append(p)
    #         else:
    #             codename = str(p).split(".")[-1]
    #             perm_obj = RolePermModel.objects.filter(codename=codename).first()
    #             if perm_obj:
    #                 resolved_objs.append(perm_obj)
    #             else:
    #                 invalid.append(p)

    #     if invalid:
    #         return Response({"error": "Invalid permissions", "invalid": invalid}, status=400)
    #     if not resolved_objs:
    #         return Response({"error": "No valid permissions provided"}, status=400)

    #     try:
    #         with transaction.atomic():
    #             # ✅ Fetch or create role-permission record
    #             role_perm_link, _ = RolePermission.objects.get_or_create(role=role_obj)

    #             # ✅ Current and new IDs
    #             current_ids = set(role_perm_link.permission.values_list('permission_id', flat=True))
    #             new_ids = [perm.permission_id for perm in resolved_objs]

    #             # ✅ Determine what to add
    #             to_add_ids = [pid for pid in new_ids if pid not in current_ids]
    #             already_assigned = list(current_ids)
    #             newly_assigned = []

    #             # ✅ Add only new permissions
    #             if to_add_ids:
    #                 role_perm_link.permission.add(*to_add_ids)
    #                 newly_assigned = to_add_ids

    #             role_perm_link.save()

    #             # ✅ Dynamic message
    #             if newly_assigned and already_assigned:
    #                 message = f"New permissions added: {newly_assigned}. Already existed: {already_assigned}."
    #             elif newly_assigned:
    #                 message = f"New permissions assigned: {newly_assigned}"
    #             elif already_assigned:
    #                 message = f"These permissions already exist for this role: {already_assigned}"
    #             else:
    #                 message = "No permissions processed."

    #             return Response({
    #                 "message": message,
    #                 "already_assigned": already_assigned,
    #                 "newly_assigned": newly_assigned
    #             }, status=200)

    #     except IntegrityError:
    #         logger.exception("DB integrity error while assigning permissions")
    #         return Response({"error": "DB integrity error while assigning permissions"}, status=400)
    #     except Exception as e:
    #         logger.exception("Unexpected error assigning permissions: %s", e)
    #         return Response({"error": str(e)}, status=500)


    # def put(self, request, role_id):
    #     self.permission_required = "update_roles"
    #     if not HasRolePermission().has_permission(request, self.permission_required):
    #         return Response({'error': 'Permission denied.'}, status=403)

    #     raw = request.data.get("permission")
    #     if raw is None:
    #         return Response({"error": "permission field is required"}, status=400)

    #     # Normalize input
    #     if isinstance(raw, list):
    #         perms_input = raw
    #     elif isinstance(raw, str):
    #         try:
    #             parsed = json.loads(raw)
    #             perms_input = parsed if isinstance(parsed, list) else [parsed]
    #         except Exception:
    #             perms_input = [p.strip() for p in raw.split(",") if p.strip()]
    #     else:
    #         perms_input = [raw]

    #     role_obj = Role.objects.filter(role_id=role_id).first()
    #     if not role_obj:
    #         return Response({"error": "Role not found."}, status=404)

    #     from roles_creation.models import Permission as RolePermModel

    #     resolved_objs = []
    #     invalid = []

    #     for p in perms_input:
    #         if isinstance(p, int) or (isinstance(p, str) and p.isdigit()):
    #             pid = int(p)
    #             perm_obj = RolePermModel.objects.filter(permission_id=pid).first()
    #             if perm_obj:
    #                 resolved_objs.append(perm_obj)
    #                 continue
    #             invalid.append(p)
    #         else:
    #             codename = str(p).split(".")[-1]
    #             perm_obj = RolePermModel.objects.filter(codename=codename).first()
    #             if perm_obj:
    #                 resolved_objs.append(perm_obj)
    #             else:
    #                 invalid.append(p)

    #     if invalid:
    #         return Response({"error": "Invalid permissions", "invalid": invalid}, status=400)

    #     new_ids = [perm.permission_id for perm in resolved_objs]

    #     with transaction.atomic():
    #         role_perm_link, _ = RolePermission.objects.get_or_create(role=role_obj)

    #         # 🔥 Replace old permissions (SELECT + DESELECT)
    #         role_perm_link.permission.set(new_ids)

    #         role_perm_link.save()

    #         return Response({
    #             "message": "Permissions updated successfully",
    #             "final_permissions": new_ids
    #         }, status=200)

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

        role_obj = Role.objects.filter(role_id=role_id).first()
        if not role_obj:
            return Response({"error": "Role not found"}, status=404)

        try:
            with transaction.atomic():
                # Get or create the RolePermission link
                role_perm_link, created = RolePermission.objects.get_or_create(role=role_obj)
                
                updated_fields = []

                # ✅ Handle is_active update
                if 'is_active' in request.data:
                    is_active = request.data.get('is_active')
                    if isinstance(is_active, bool) or str(is_active).lower() in ['true', 'false', '1', '0']:
                        role_perm_link.is_active = bool(is_active) if isinstance(is_active, bool) else str(is_active).lower() in ['true', '1']
                        updated_fields.append('is_active')

                # ✅ Handle permission updates
                raw = request.data.get("permission")
                if raw is not None:
                    # Normalize input
                    if isinstance(raw, list):
                        perms_input = raw
                    elif isinstance(raw, str):
                        try:
                            parsed = json.loads(raw)
                            perms_input = parsed if isinstance(parsed, list) else [parsed]
                        except:
                            perms_input = [p.strip() for p in raw.split(",") if p.strip()]
                    else:
                        perms_input = [raw]

                    from roles_creation.models import Permission
                    resolved = []
                    invalid = []

                    for p in perms_input:
                        if str(p).isdigit():
                            obj = Permission.objects.filter(permission_id=int(p)).first()
                        else:
                            codename = str(p).split(".")[-1]
                            obj = Permission.objects.filter(codename=codename).first()

                        if obj:
                            resolved.append(obj)
                        else:
                            invalid.append(p)

                    if invalid:
                        return Response({"error": "Invalid permissions", "invalid": invalid}, status=400)
                    
                    if resolved:
                        current_ids = set(role_perm_link.permission.values_list('permission_id', flat=True))
                        new_ids = [p.permission_id for p in resolved]
                        
                        to_add = [pid for pid in new_ids if pid not in current_ids]
                        already = [pid for pid in new_ids if pid in current_ids]
                        
                        if to_add:
                            role_perm_link.permission.add(*Permission.objects.filter(permission_id__in=to_add))
                            updated_fields.append('permissions')

                # ✅ Save changes
                if updated_fields:
                    role_perm_link.save()
                    return Response({
                        "message": f"Updated: {', '.join(updated_fields)}",
                        "is_active": role_perm_link.is_active,
                        "permission_count": role_perm_link.permission.count()
                    }, status=200)
                else:
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
        """ Handle GET requests to fetch all user-role associations """
        self.permission_required = "view_roles"
        if not HasRolePermission().has_permission(request, self.permission_required):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
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