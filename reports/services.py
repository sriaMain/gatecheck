 
from add_visitors.models import VisitorLog
from django.db.models import Q
 

 
def get_visitors_by_date_range(from_date, to_date, filters=None):
    queryset = VisitorLog.objects.filter(created_at__range=(from_date, to_date))
 
    if filters:
        if filters.get("host_name"):
            queryset = queryset.filter(host_name=filters["host_name"])
        if filters.get("category"):
            queryset = queryset.filter(category=filters["category"])
 
    return queryset
 
 