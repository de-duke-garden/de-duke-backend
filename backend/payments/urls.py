from rest_framework.routers import DefaultRouter
from .views import FlutterwavePaymentViewSet


router = DefaultRouter()
router.register(r'flutterwave', FlutterwavePaymentViewSet, basename='flutterwave')
urlpatterns = router.urls