from django.contrib import admin
from . import models
from django.contrib.gis.db import models as gis_models
import mapwidgets
import nested_admin


class PropertyAdminInlineProxy:
    def has_add_permission(self, request, obj=None):
        # Allow adding only if the user has a StakeholderAccount
        if request.user.is_stakeholder():
            if obj and request.user.stakeholder_account != obj.listed_by:
                return False
            return True
        return False  # Deny add permission if no StakeholderAccount

    def get_readonly_fields(self, request, obj=None):
        # Make all fields readonly if the user does not own the property
        if obj and (not self.has_add_permission(request, obj) or (
            self.has_add_permission(
                request, obj) and request.user.stakeholder_account != obj.listed_by
        )):
            return [field.name for field in self.model._meta.fields]
        return []  # No readonly fields if the user has permission

    def has_delete_permission(self, request, obj=None):
        # Allow deleting only if the user owns the property
        return self.has_add_permission(request, obj)


class PropertyImageInline(PropertyAdminInlineProxy, nested_admin.NestedTabularInline):
    model = models.PropertyImage
    extra = 0
    max_num = 5
    min_num = 1
    fields = ('image', 'is_primary')


class HomePropertyBedroomInline(PropertyAdminInlineProxy, nested_admin.NestedTabularInline):
    model = models.HomePropertyBedroom
    extra = 0
    min_num = 1
    fields = ('level', 'dimention_width', 'dimention_length')


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
        if not change:
            obj.listed_by = request.user.stakeholder_account
        return super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        # Check if the user has a StakeholderAccount
        if request.user.is_stakeholder():
            return True
        return False  # Deny add permission if no StakeholderAccount

    def get_exclude(self, request, obj=None):
        exclude = ['property_type']
        # if obj is None:
        #     exclude.extend(['address', 'listed_by'])
        return exclude

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = {'address', 'listed_by'}

        if obj and (not self.has_add_permission(request) or (
            self.has_add_permission(
                request) and request.user.stakeholder_account != obj.listed_by
        )):
            # Gray out all fields except `readable` if the admin is not the owner of the property
            readable = ['is_active', 'last_checked']

            # Get only actual model fields (exclude related fields like ManyToOneRel)
            all_fields = [
                field.name for field in self.model._meta.get_fields() if not field.is_relation]

            # Add all fields except the readable ones to readonly_fields
            readonly_fields.update(
                field for field in all_fields if field not in readable)

        return sorted(readonly_fields)


@admin.register(models.HomeProperty)
class HomeProperty(PropertyAdminProxy, nested_admin.NestedModelAdmin):
    inlines = [HomePropertyBedroomInline, PropertyImageInline]


@admin.register(models.ApartmentProperty)
class ApartmentProperty(PropertyAdminProxy, nested_admin.NestedModelAdmin):
    inlines = [PropertyImageInline]


@admin.register(models.BannedProperty)
class BannedPropertyAdmin(admin.ModelAdmin):
    readonly_fields = ('banned_by',)

    def save_model(self, request, obj, form, change):
        if not hasattr(obj, 'banned_by') or (hasattr(obj, 'banned_by') and obj.banned_by is None):
            obj.banned_by = request.user
        return super().save_model(request, obj, form, change)


@admin.register(models.VerifiedProperty)
class VerifiedPropertyAdmin(admin.ModelAdmin):
    readonly_fields = ('verified_by',)

    def save_model(self, request, obj, form, change):
        if not hasattr(obj, 'verified_by') or (hasattr(obj, 'verified_by') and obj.verified_by is None):
            obj.verified_by = request.user
        return super().save_model(request, obj, form, change)
