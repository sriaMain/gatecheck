from django.contrib import admin
from .models import CustomUser, Company
from django.contrib.auth.admin import UserAdmin

admin.site.register(CustomUser, UserAdmin)

admin.site.register(Company)
# admin.site.register(CustomUser)
