from rest_framework.routers import DefaultRouter
from django.urls import path
from . import views


router = DefaultRouter()

router.register('interested', views.InterestedPropertyViewSet, basename='interested-property')
router.register('host/homes/bedrooms', views.HostHomePropertyBedroomViewSet, basename='host-home-property-bedroom')
router.register('host/property/images', views.HostPropertyImageViewSet, basename='host-property-image')
router.register('host/apartments', views.HostApartmentPropertyViewSet, basename='host-apartment-property')
router.register('host/homes', views.HostHomePropertyViewSet, basename='host-home-property')
router.register('bookmarks', views.BookmarkedPropertyViewSet, basename='bookmarked-property')
router.register('', views.PropertyViewSet, basename='property')


urlpatterns = [
    path("field-choices/", views.PropertyFieldChoicesView.as_view(), name="property-choices")
] + router.urls
