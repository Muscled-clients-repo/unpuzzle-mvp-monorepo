"""
Filters for puzzle reflection API.
"""
import django_filters
from django.db.models import Q
from .models import PuzzleReflection, ReflectionType


class PuzzleReflectionFilter(django_filters.FilterSet):
    """Filter set for puzzle reflections"""
    
    video_id = django_filters.CharFilter(lookup_expr='icontains')
    reflection_type = django_filters.ChoiceFilter(choices=ReflectionType.choices)
    has_media_file = django_filters.BooleanFilter(method='filter_has_media_file')
    has_loom_link = django_filters.BooleanFilter(method='filter_has_loom_link')
    date_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = PuzzleReflection
        fields = ['video_id', 'reflection_type', 'course']
    
    def filter_has_media_file(self, queryset, name, value):
        """Filter by presence of media file"""
        if value:
            return queryset.filter(media_file__isnull=False)
        return queryset.filter(media_file__isnull=True)
    
    def filter_has_loom_link(self, queryset, name, value):
        """Filter by presence of loom link"""
        if value:
            return queryset.exclude(loom_link__in=['', None])
        return queryset.filter(Q(loom_link='') | Q(loom_link__isnull=True))
    
    def filter_search(self, queryset, name, value):
        """Search across title, description, and text content"""
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(text_content__icontains=value)
        )