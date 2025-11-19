from django.contrib import admin

# Register your models here.

from .models import Visitor, Company, Category, Vehicle, VisitorLog

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # list_display = ['name', 'description', 'created_at']
    search_fields = ['name']
    # list_filter = ['created_at', 'is_active']

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['vehicle_number', 'vehicle_type', 'model', 'color']
    search_fields = ['vehicle_number', 'model']
    # list_filter = ['vehicle_type', 'created_at']

@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    # list_display = ['pass_id', 'visitor_name', 'mobile_number', 'visiting_date', 'status', 'is_inside']
    search_fields = ['visitor_name', 'mobile_number', 'pass_id']
    # list_filter = ['status', 'visiting_date', 'is_inside', 'recurring_pass', 'gender']
    readonly_fields = ['pass_id', 'created_at', 'updated_at']

@admin.register(VisitorLog)
class VisitorLogAdmin(admin.ModelAdmin):
    # list_display = ['visitor', 'action', 'timestamp', 'gate_number', 'security_guard']
    search_fields = ['visitor__visitor_name', 'visitor__pass_id']
    # list_filter = ['action', 'timestamp']
    # readonly_fields = ['timestamp']