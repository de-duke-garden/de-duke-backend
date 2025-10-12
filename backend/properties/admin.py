from django.contrib import admin
from . import models
from django.contrib.gis.db import models as gis_models
import mapwidgets
import nested_admin
import googlemaps
from django.conf import settings
import logging
from properties.models import Property

logger = logging.getLogger("django")


# class PropertyAdminInlineProxy:
#     def has_add_permission(self, request, obj=None):
#         # Allow adding only if the user has a HostAccount
#         if request.user.is_host():
#             if obj and request.user.host_account != obj.listed_by:
#                 return False
#             return True
#         return False  # Deny add permission if no HostAccount

#     def get_readonly_fields(self, request, obj=None):
#         # Make all fields readonly if the user does not own the property
#         if obj and (not self.has_add_permission(request, obj) or (
#             self.has_add_permission(
#                 request, obj) and request.user.host_account != obj.listed_by
#         )):
#             return [field.name for field in self.model._meta.fields]
#         return []  # No readonly fields if the user has permission

#     def has_delete_permission(self, request, obj=None):
#         # Allow deleting only if the user owns the property
#         return self.has_add_permission(request, obj)


class PropertyImageInline(
    # PropertyAdminInlineProxy, 
    nested_admin.NestedTabularInline):
    model = models.PropertyImage
    extra = 0
    max_num = 5
    min_num = 1
    fields = ('image', 'is_primary')


class CommercialPropertyRoomInline(
    # PropertyAdminInlineProxy, 
    nested_admin.NestedTabularInline):
    model = models.CommercialPropertyRoom
    extra = 0
    min_num = 0
    fields = ('level', 'dimention_width', 'dimention_length')

class VerifiedPropertyInline(nested_admin.NestedStackedInline):
    model = models.VerifiedProperty
    extra = 0
    max_num = 1
    min_num = 0
    readonly_fields = ('verified_by', 'created_at')


class BannedPropertyInline(nested_admin.NestedTabularInline):
    model = models.BannedProperty
    extra = 0
    max_num = 1
    min_num = 0
    readonly_fields = ('banned_by', 'created_at')


class PropertyAdminProxy:
    formfield_overrides = {
        gis_models.PointField: {"widget": mapwidgets.GoogleMapPointFieldWidget(
            attrs={
                'style': 'width: 100%; height: 400px;',
                'map_options': {
                    'zoom': 15,
                    'center': {'lat': 0, 'lng': 0},
                },
            }
        )}
    }

    def save_model(self, request, obj, form, change):
        # if not change:
        #     obj.listed_by = request.user.host_account
        """
        Override the save method to reverse geocode the location into an address
        only if the location has changed.
        """
        def _update_address():
            gmaps = googlemaps.Client(key=settings.GOOGLE_MAP_API_KEY)

            # Extract latitude and longitude from the PointField
            latitude = obj.location.y
            longitude = obj.location.x

            try:
                # Perform reverse geocoding
                result = gmaps.reverse_geocode((latitude, longitude))
                if result:
                    # Extract the formatted address from the response
                    obj.address = result[0]['formatted_address']
            except Exception as e:
                # Log the error if reverse geocoding fails
                logger.error(f"Error during reverse geocoding: {e}")

            # Check if the instance already exists in the database
        if change:
            # Fetch the existing instance from the database
            existing_instance = Property.objects.get(id=obj.id)
            # Compare the current location with the existing location
            if existing_instance and obj.location != existing_instance.location:
                _update_address()
        else:
            # For new instances, always perform reverse geocoding
            if obj.location:
                _update_address()
        return super().save_model(request, obj, form, change)

    # def has_add_permission(self, request):
    #     # Check if the user has a HostAccount
    #     if request.user.is_host():
    #         return True
    #     return False  # Deny add permission if no HostAccount

    def get_exclude(self, request, obj=None):
        exclude = ['property_type']
        # if obj is None:
        #     exclude.extend(['address', 'listed_by'])
        return exclude

    # def get_readonly_fields(self, request, obj=None):
    #     readonly_fields = {'address', 'listed_by'}

    #     if obj and (not self.has_add_permission(request) or (
    #         self.has_add_permission(
    #             request) and request.user.host_account != obj.listed_by
    #     )):
    #         # Gray out all fields except `readable` if the admin is not the owner of the property
    #         readable = ['is_active', 'last_checked']

    #         # Get only actual model fields (exclude related fields like ManyToOneRel)
    #         all_fields = [
    #             field.name for field in self.model._meta.get_fields() if not field.is_relation]

    #         # Add all fields except the readable ones to readonly_fields
    #         readonly_fields.update(
    #             field for field in all_fields if field not in readable)

    #     return sorted(readonly_fields)


@admin.register(models.CommercialProperty)
class CommercialProperty(PropertyAdminProxy, nested_admin.NestedModelAdmin):
    inlines = [CommercialPropertyRoomInline, PropertyImageInline, VerifiedPropertyInline, BannedPropertyInline]

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, models.VerifiedProperty):
                instance.verified_by = request.user
            elif isinstance(instance, models.BannedProperty):
                instance.banned_by = request.user
            instance.save()
        formset.save_m2m()


@admin.register(models.ShortletProperty)
class ShortletProperty(PropertyAdminProxy, nested_admin.NestedModelAdmin):
    inlines = [PropertyImageInline, VerifiedPropertyInline, BannedPropertyInline]

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, models.VerifiedProperty):
                instance.verified_by = request.user
            elif isinstance(instance, models.BannedProperty):
                instance.banned_by = request.user
            instance.save()
        formset.save_m2m()


@admin.register(models.BannedProperty)
class BannedPropertyAdmin(admin.ModelAdmin):
    readonly_fields = ('banned_by',)

    def save_model(self, request, obj, form, change):
        obj.banned_by = request.user
        return super().save_model(request, obj, form, change)


@admin.register(models.VerifiedProperty)
class VerifiedPropertyAdmin(admin.ModelAdmin):
    readonly_fields = ('verified_by',)

    def save_model(self, request, obj, form, change):
        obj.verified_by = request.user
        return super().save_model(request, obj, form, change)


@admin.register(models.InterestedProperty)
class InterestedPropertyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # InterestedProperty should not be added via admin
        return False

    def has_change_permission(self, request, obj=None):
        # InterestedProperty should not be changed via admin
        return False