from django.contrib import admin
from .models import CustomUser, Company
from django.contrib.auth.admin import UserAdmin

admin.site.register(CustomUser, UserAdmin)

# class CustomUserAdmin(UserAdmin):
#     model = CustomUser
#     list_display = ['email', 'username', 'company_name', 'is_staff', 'is_active']
#     list_filter = ['is_staff', 'is_active', 'company']
#     fieldsets = (
#         (None, {'fields': ('email', 'username', 'password', 'company')}),
#         ('Permissions', {'fields': ('is_staff', 'is_active')}),
#     )
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('email', 'username', 'company', 'password1', 'password2', 'is_staff', 'is_active')}
#         ),
#     )
#     search_fields = ('email', 'username')
#     ordering = ('email',)
admin.site.register(Company)
# admin.site.register(CustomUser)
