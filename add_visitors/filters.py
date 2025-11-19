import django_filters
from django.db.models import Q
from .models import Visitor

class VisitorFilter(django_filters.FilterSet):
    """Advanced filtering for visitors"""
    
    search = django_filters.CharFilter(method='filter_search')
    date_range = django_filters.DateFromToRangeFilter(field_name='visiting_date')
    status = django_filters.MultipleChoiceFilter(choices=Visitor.PassStatus.choices)
    is_inside = django_filters.BooleanFilter()
    
    class Meta:
        model = Visitor
        fields = ['status', 'category', 'pass_type', 'is_inside']
    
    def filter_search(self, queryset, name, value):
        """Search across multiple fields"""
        return queryset.filter(
            Q(visitor_name__icontains=value) |
            Q(mobile_number__icontains=value) |
            Q(pass_id__icontains=value) |
            Q(whom_to_meet__icontains=value)
        )