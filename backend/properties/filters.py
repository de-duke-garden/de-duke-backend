from django_filters import rest_framework as filters
from django.db.models import F, Count, Q
from . import models


class PropertyFilter(filters.FilterSet):
    """
    Custom filter set for properties.
    This filter set allows filtering properties based on various criteria.
    """
    commercialproperty__total_rooms = filters.RangeFilter(method='filter_rooms')
    commercialproperty__total_bathrooms = filters.RangeFilter(method='filter_bathrooms')
    search = filters.CharFilter(
        field_name='search',
        method='filter_search',
        label='Search',
        help_text='Search properties by description and address.'
    )
    
    class Meta:
        model = models.Property
        fields = {
            'property_type': ['exact'],
            'created_at': ['gte', 'lte'],
            'updated_at': ['gte', 'lte'],
            'commercialproperty__price': ['gte', 'lte'],
            'commercialproperty__commercial_type': ['exact', 'in'],
            'commercialproperty__listing_type': ['exact', 'in'],
            'commercialproperty__architectural_style': ['exact', 'in'],
            'commercialproperty__property_condition': ['exact', 'in'],
            'shortletproperty__price': ['gte', 'lte'],
            'shortletproperty__shortlet_type': ['exact', 'in'],
        }
    
    def filter_rooms(self, queryset, name, value):
        """
        Custom filter for commercial properties total rooms.
        Filters properties based on the range of total rooms count.
        """
        # Annotate with room count
        queryset = queryset.annotate(
            room_count=Count('commercialproperty__rooms')
        )
        
        if value.start is not None:
            queryset = queryset.filter(room_count__gte=value.start)
        if value.stop is not None:
            queryset = queryset.filter(room_count__lte=value.stop)
        return queryset
    
    def filter_bathrooms(self, queryset, name, value):
        """
        Custom filter for total bathrooms.
        Filters properties based on the range of total bathrooms.
        """
        
        if value.start is not None:
            queryset = queryset.filter(total_bathrooms__gte=value.start)
        if value.stop is not None:
            queryset = queryset.filter(total_bathrooms__lte=value.stop)
        
        return queryset
    
    def filter_search(self, queryset, name, value):
        """
        Custom search filter.
        Filters properties based on description and address.
        """
        if not value:
            return queryset
        
        # Use icontains for case-insensitive search
        return queryset.filter(
            Q(description__icontains=value) |
            Q(address__icontains=value)
        )