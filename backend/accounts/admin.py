import nested_admin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import OTPRequest, User, PhoneNumber, GoogleAccount, StakeholderAccount, GovIssuedIdentity


admin.site.site_header = "De-Duke Garden Care"
admin.site.site_title = "De-Duke Garden Care administration"
admin.site.index_title = "Welcome to De-Duke Admin Dashboard"


class PhoneNumberInline(nested_admin.NestedTabularInline):
    model = PhoneNumber
    extra = 0
    max_num = 1


class GoogleAccountInline(nested_admin.NestedTabularInline):
    model = GoogleAccount
    extra = 0
    max_num = 1


class GovIssuedIdentityInline(nested_admin.NestedTabularInline):
    model = GovIssuedIdentity
    extra = 0
    max_num = 1


class StakeholderAccountInline(nested_admin.NestedTabularInline):
    model = StakeholderAccount
    extra = 0
    max_num = 1
    inlines = [GovIssuedIdentityInline]


@admin.register(User)
class UserAdmin(BaseUserAdmin, nested_admin.NestedModelAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "email_verified",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "password1", "password2"),
            },
        ),
    )
    list_display = ("email", "first_name", "last_name", "is_staff")
    search_fields = ("first_name", "last_name", "email")
    ordering = ("email",)
    inlines = [PhoneNumberInline, GoogleAccountInline, StakeholderAccountInline]


@admin.register(OTPRequest)
class OTPRequestAdmin(nested_admin.NestedModelAdmin):
    list_display = ("ref", "otp", "is_verified", "has_expired", "created_at")
    search_fields = ("ref",)
    ordering = ("-created_at",)
    list_filter = ("created_at",)