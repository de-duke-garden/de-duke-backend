from django.urls import path
from .views import UserViewSet, UserMeViewSet, PasswordResetViewSet, EmailVerificationViewSet
from rest_framework.routers import DefaultRouter


router = DefaultRouter()

router.register(r'', UserViewSet, basename='user')
router.register('me', UserMeViewSet, basename='current-user')
router.register('password-reset', PasswordResetViewSet, basename='password-reset')
router.register('verify-email', EmailVerificationViewSet, basename='verify-email')

urlpatterns = router.urls
