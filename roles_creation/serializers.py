from rest_framework import serializers
from .models import Role, Permission, RolePermission,UserRole
from  .models import Permission
from .models import RolePermission


class RoleSerializer(serializers.ModelSerializer):
    # roles = serializers.SerializerMethodField()
    created_by = serializers.SlugRelatedField(
        read_only=True, slug_field='username'
    )
    modified_by = serializers.SlugRelatedField(
        read_only=True, slug_field='username'
    )
    class Meta:
        model = Role
        fields = '__all__'


    # def validate_name(self, value):

    #     normalized_name = value.strip()

    #     if Role.objects.filter(name__iexact=normalized_name).exists():

    #         raise serializers.ValidationError("A role with this name already exists.")

    #     return normalized_name

    def validate_name(self, value):
        normalized = value.strip()

        # Get current object's primary key
        pk = self.instance.role_id if self.instance else None

        # Check duplicates excluding current record
        if Role.objects.filter(name__iexact=normalized).exclude(role_id=pk).exists():
            raise serializers.ValidationError("A role with this name already exists.")

        return normalized


 

class PermissionSerializer(serializers.ModelSerializer):
    created_by = serializers.SlugRelatedField(
        read_only=True, slug_field='username'
    )
    modified_by = serializers.SlugRelatedField(
        read_only=True, slug_field='username'
    )
   
    # created_by = serializers.SerializerMethodField()

    class Meta:
        model = Permission
        fields = ['permission_id','name','is_active', 'created_at', 'modified_at','created_by', 'modified_by']

        read_only_fields = ['created_by']
 


class RolePermissionSerializer(serializers.ModelSerializer):
    permission = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(), many=True, required=False
    )

    class Meta:
        model = RolePermission
        fields = ["role", "permission","role_permission_id", "is_active"]

    def validate_permission(self, value):
        """
        Handle the 'all' keyword in the request and ensure proper IDs.
        """
        request = self.context.get("request")
        if request:
            raw_permission_data = request.data.get("permission", [])

            if isinstance(raw_permission_data, list) and "all" in raw_permission_data:
                return Permission.objects.all()

        return value

    def create(self, validated_data):
        # Pop permission data
        permission_data = validated_data.pop("permission", [])

        # Extract IDs from Permission instances if needed
        permission_ids = [
            perm.pk if isinstance(perm, Permission) else int(perm)
            for perm in permission_data
        ]

        # Create the RolePermission instance
        instance = RolePermission.objects.create(**validated_data)

        # Set permissions using IDs
        instance.permission.set(permission_ids)

        return instance

    def to_representation(self, instance):
        """
        Display role name and permission names in response.
        """
        rep = super().to_representation(instance)
        rep["role"] = instance.role.name
        rep["permission"] = list(instance.permission.values_list("name", flat=True))
        return rep






class UserRoleSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    company_id = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    created_by = serializers.SlugRelatedField(read_only=True, slug_field='username')
    modified_by = serializers.SlugRelatedField(read_only=True, slug_field='username')

    class Meta:
        model = UserRole
        fields = [
            'user_role_id',
            'user',          # ID
            'role',          # ID
            'user_name',     # readable
            'role_name',     # readable
            'created_by',
            'modified_by',
            'created_at',
            'modified_at',
            'assigned_at',
            'is_active',
            'company_id',
            'company_name',
        ]

    def get_company_id(self, obj):
        # Try to get company_id from user relation
        if hasattr(obj.user, 'company') and obj.user.company:
            return obj.user.company.id
        return None

    def get_company_name(self, obj):
        # Try to get company_name from user relation
        if hasattr(obj.user, 'company') and obj.user.company:
            return obj.user.company.company_name
        return None