# def serialize_visitors(queryset):
#     data = []
#     for v in queryset:
#         data.append({
#             "Name": getattr(v, "visitor_id.name", ""),
#             "Email": getattr(v, "visitor_id.email", ""),
#             "Mobile": getattr(v, "mobile", ""),
#             "Whom to Meet": getattr(v, "whom_to_meet", ""),
#             "Visit Date": v.created_at.date() if v.created_at else "",
#             "Time In": getattr(v, "time_in", ""),
#             "Time Out": getattr(v, "time_out", ""),
#             "Duration": getattr(v, "duration", ""),
#             "Access Card": getattr(v, "access_card", ""),
#             "Category": getattr(v, "category", ""),
#         })
#     return data
 

 # reports/serializers.py

from rest_framework import serializers
from add_visitors.models import Visitor
from user_onboarding.models import Company

class BulkVisitorSerializer(serializers.ModelSerializer):
    coming_from = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        allow_null=True,
        required=False
    )

    class Meta:
        model = Visitor
        fields = [
            'visitor_name', 'mobile_number', 'visiting_date', 'visiting_time',
            'category', 'coming_from', 'email_id', 'pass_type', 'gender', 'purpose_of_visit'
        ]
        extra_kwargs = {
            'gender': {'required': False},
            'purpose_of_visit': {'required': True},
        }


from add_visitors.models import Visitor

# def serialize_visitors(queryset):
#     data = []
#     for v in queryset:
#         visitor_obj = None

#         # Try to get Visitor object if visitor_id is set
#         if getattr(v, "visitor_id", None):
#             try:
#                 visitor_obj = Visitor.objects.get(pk=v.visitor_id)
#             except Visitor.DoesNotExist:
#                 visitor_obj = None

#         data.append({
#             "Name": visitor_obj.visitor_name if visitor_obj else "",
#             "Email": visitor_obj.email_id if visitor_obj else "",
#             "Mobile": visitor_obj.mobile_number if visitor_obj else "",
#             "Whom to Meet": getattr(v, "whom_to_meet", ""),
#             "Visit Date": v.created_at.date() if getattr(v, "created_at", None) else "",
#             "Time In": getattr(v, "time_in", ""),
#             "Time Out": getattr(v, "time_out", ""),
#             # "Duration": getattr(v, "duration", ""),
#             "Access Card": visitor_obj.pass_id if visitor_obj else "",
#             "Category": visitor_obj.category.name if visitor_obj and visitor_obj.category else "",
#         })
#     return data

def serialize_visitors(queryset):
    data = []
    for v in queryset:
        visitor_obj = v  # v IS the Visitor instance

        data.append({
            "Name": visitor_obj.visitor_name,
            "Email": visitor_obj.email_id,
            "Mobile": visitor_obj.mobile_number,
            "Whom to Meet": visitor_obj.whom_to_meet,
            "Visit Date": visitor_obj.visiting_date,
            "Time In": visitor_obj.entry_time,
            "Time Out": visitor_obj.exit_time,
            "Access Card": visitor_obj.pass_id,
            "Category": visitor_obj.category.name if visitor_obj.category else "",
        })
    return data

