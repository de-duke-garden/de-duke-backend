from django.urls import path
from . import views

urlpatterns = [
    path("basic/login/", views.BasicAuthView.as_view(), name="basic_login"),
    path("basic/login/refresh/", views.BasicAuthRefreshView.as_view(), name="basic_login_refresh"),
    path("basic/login/verify/", views.BasicAuthVerifyView.as_view(), name="basic_login_verify"),
]