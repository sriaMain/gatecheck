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

class BulkVisitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = [
            'visitor_name', 'mobile_number', 'visiting_date', 'visiting_time',
            'category', 'coming_from', 'email_id', 'pass_type', 'gender'  # include all fields you upload
        ]
        extra_kwargs = {
            'gender': {'required': False},  # Make gender optional here
        }


from add_visitors.models import Visitor

def serialize_visitors(queryset):
    data = []
    for v in queryset:
        visitor_obj = None

        # Try to get Visitor object if visitor_id is set
        if getattr(v, "visitor_id", None):
            try:
                visitor_obj = Visitor.objects.get(pk=v.visitor_id)
            except Visitor.DoesNotExist:
                visitor_obj = None

        data.append({
            "Name": visitor_obj.visitor_name if visitor_obj else "",
            "Email": visitor_obj.email_id if visitor_obj else "",
            "Mobile": visitor_obj.mobile_number if visitor_obj else "",
            "Whom to Meet": getattr(v, "whom_to_meet", ""),
            "Visit Date": v.created_at.date() if getattr(v, "created_at", None) else "",
            "Time In": getattr(v, "time_in", ""),
            "Time Out": getattr(v, "time_out", ""),
            # "Duration": getattr(v, "duration", ""),
            "Access Card": visitor_obj.pass_id if visitor_obj else "",
            "Category": visitor_obj.category.name if visitor_obj and visitor_obj.category else "",
        })
    return data



# def serialize_visitors(queryset):
#     data = []
#     for v in queryset:
#         visitor_obj = Visitor.objects.filter(pk=v.visitor_id).first()
#         data.append({
#             "name": visitor_obj.visitor_name if visitor_obj else "",
#             "email": visitor_obj.email_id if visitor_obj else "",
#             "mobile": visitor_obj.mobile_number if visitor_obj else "",
#             "whom_to_meet": v.whom_to_meet,
#             "visit_date": v.created_at.date() if v.created_at else "",
#             "time_in": v.time_in,
#             "time_out": v.time_out,
#             "duration": v.duration,
#             "access_card": visitor_obj.pass_id if visitor_obj else "",
#             "category": visitor_obj.category.name if visitor_obj and visitor_obj.category else "",
#         })
#     return data
