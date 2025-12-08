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


def serialize_visitors(queryset):
    data = []
    for v in queryset:

        # Ensure v is a Visitor instance
        visitor_obj = v if hasattr(v, "visitor_name") else None

        data.append({
            "Name": getattr(visitor_obj, "visitor_name", ""),
            "Email": getattr(visitor_obj, "email_id", ""),
            "Mobile": getattr(visitor_obj, "mobile_number", ""),
            "Whom to Meet": getattr(visitor_obj, "whom_to_meet", ""),
            "Visit Date": getattr(visitor_obj, "visiting_date", ""),
            "Time In": getattr(visitor_obj, "entry_time", ""),
            "Time Out": getattr(visitor_obj, "exit_time", ""),
            "Access Card": getattr(visitor_obj, "pass_id", ""),
            "Category": getattr(visitor_obj.category, "name", "") 
                        if getattr(visitor_obj, "category", None) else "",
        })

    return data


