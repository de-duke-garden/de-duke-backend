from django.contrib import admin
from django.urls import path, include, reverse, reverse_lazy
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import permissions


urlpatterns = [
    path("", RedirectView.as_view(url=reverse_lazy("docs"))),
    path("payments/", include('payments.urls'), name="payments"),
    path("properties/", include('properties.urls'), name="properties"),
    path("accounts/", include('accounts.urls'), name="accounts"),
    path("api-auth/", include('api_auth.urls'), name="api-auth"),
    path("auth/", include('rest_framework.urls'), name="auth"),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT)
