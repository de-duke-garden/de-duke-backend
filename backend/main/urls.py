"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, reverse, reverse_lazy
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="De-Duke API",
        default_version='v1',
        description="""**De-Duke Garden Care** is envisioned as a comprehensive online platform designed to streamline property transactions by connecting property owners, landlords, and potential tenants or buyers.""",
        terms_of_service="https://www.yourapp.com/terms/",
        contact=openapi.Contact(email="khidirahmad05@gmail.com",
                                name="Ahmad Khidir",
                                url="https://linkedin.com/in/ahmadkhidir/"),
        license=openapi.License(name="De-Duke License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("", RedirectView.as_view(url=reverse_lazy("docs"))),
    path("accounts/", include('accounts.urls'), name="accounts"),
    path("api-auth/", include('api_auth.urls'), name="api-auth"),
    path("auth/", include('rest_framework.urls'), name="auth"),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='docs'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT)
