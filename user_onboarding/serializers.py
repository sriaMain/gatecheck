from rest_framework import serializers
from user_onboarding.models import Company, CustomUser
from django.contrib.auth.hashers import make_password
from roles_creation.models import Role  # Assuming Role model is in roles_creation ap
from roles_creation.serializers import RoleSerializer

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model= Company
        fields = ['id', 'company_name', 'address', 'location', 'pin_code']
    



class CustomUserSerializer(serializers.ModelSerializer):
   
    
    roles = serializers.SerializerMethodField()
    
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(), write_only=True
    )
 
    company_name = serializers.SlugRelatedField(
        source='company',
        slug_field='company_name',
        read_only=True
    )
  


    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'company', 'mobile_number', 'alias_name', 'block', 'floor', 'company_name', 'username', 'roles', 'is_active']  # no user_id/password
        extra_kwargs = {
            'email': {'required': True},
            # 'role': {'required': True},  # Allow blank role
            'username': {'required': True},  # Allow blank username
            
        }
    

    def create(self, validated_data):  # ✅ Make sure this parameter exists
        raw_password = validated_data['password']
        # role = validated_data.pop('role', None)
        user_id = f"USR{CustomUser.objects.count() + 1:05}"  # just an example

        user = CustomUser.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            user_id=user_id,
            password=make_password(raw_password),
            company=validated_data['company'],
            mobile_number=validated_data.get('mobile_number', ''),
            alias_name=validated_data.get('alias_name', ''),
            block=validated_data.get('block', ''),
            floor=validated_data.get('floor', ''),
            # role = validated_data.get('role', None),
       
        )
        return user
    
    def get_roles(self, obj):
        return [ur.role.name for ur in obj.user_roles.filter(is_active=True)]
        # return [role.name for role in obj.roles.all()]
    
   