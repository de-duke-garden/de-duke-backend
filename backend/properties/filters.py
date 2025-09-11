from django_filters import rest_framework as filters
from django.db.models import F, Count, Q
from . import models


class PropertyFilter(filters.FilterSet):
    """
    Custom filter set for properties.
    This filter set allows filtering properties based on various criteria.
    """
    homeproperty__total_bedrooms = filters.RangeFilter(method='filter_bedrooms')
    homeproperty__total_bathrooms = filters.RangeFilter(method='filter_bathrooms')
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
            'homeproperty__price': ['gte', 'lte'],
            'homeproperty__home_type': ['exact', 'in'],
            'homeproperty__list_type': ['exact', 'in'],
            'homeproperty__architectural_style': ['exact', 'in'],
            'homeproperty__property_condition': ['exact', 'in'],
            'apartmentproperty__price': ['gte', 'lte'],
            'apartmentproperty__apartment_type': ['exact', 'in'],
        }
    
    def filter_bedrooms(self, queryset, name, value):
        """
        Custom filter for total bedrooms.
        Filters properties based on the range of total bedrooms count.
        """
        # Annotate with bedroom count
        queryset = queryset.annotate(
            bedroom_count=Count('homeproperty__bedrooms')
        )
        
        if value.start is not None:
            queryset = queryset.filter(bedroom_count__gte=value.start)
        if value.stop is not None:
            queryset = queryset.filter(bedroom_count__lte=value.stop)
        return queryset
    
    def filter_bathrooms(self, queryset, name, value):
        """
        Custom filter for total bathrooms.
        Filters properties based on the range of total bathrooms (half + full).
        """
        # Only filter if both half and full bathroom fields are not null
        queryset = queryset.filter(
            homeproperty__total_half_bathrooms__isnull=False,
            homeproperty__total_full_bathrooms__isnull=False
        ).annotate(
            total_bathrooms=F('homeproperty__total_half_bathrooms') + F('homeproperty__total_full_bathrooms')
        )
        
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