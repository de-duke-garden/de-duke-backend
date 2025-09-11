from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import parsers
from rest_framework.views import APIView
from django.db.models import Q
from django.core.files.uploadedfile import InMemoryUploadedFile
from django_filters import rest_framework as rest_filters
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from django.utils import timezone


from .utility import encrypt_payload
from . import models
from . import serializers
from . import filters


class PropertyViewSet(
    viewsets.mixins.ListModelMixin,
    viewsets.mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """
    A viewset for listing and retrieving properties.
    This viewset provides basic functionality to list all properties
    and retrieve details of a specific property.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.PropertySerializer
    filter_backends = (rest_filters.DjangoFilterBackend,)
    filterset_class = filters.PropertyFilter

    def get_queryset(self):
        """
        Returns a queryset of filtered properties.
        """
        return models.Property.objects.filter(
            Q(banned_properties__isnull=True) &
            Q(is_active=True) &
            Q(is_deleted=False)
        )

    @extend_schema(
        operation_id='Retrieve Property with Similar Properties',
        description='Retrieve a property along with a list of similar properties.',
        responses={200: serializers.PropertyWithSimilarSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        property = self.get_object()
        # Review this filter logic to ensure it meets your requirements
        similar_properties = models.Property.objects.filter(
            Q(banned_properties__isnull=True) &
            Q(is_active=True) &
            Q(is_deleted=False) &
            ~Q(id=property.id)
        ).order_by('-created_at')[:5]

        # Create an object-like structure instead of serialized data
        class PropertyWithSimilar:
            def __init__(self, property, similar_properties):
                self.property = property
                self.similar_properties = similar_properties

        property_with_similar = PropertyWithSimilar(
            property, similar_properties)
        serializer = serializers.PropertyWithSimilarSerializer(
            property_with_similar, context={'request': request})
        return Response(serializer.data)


class BookmarkedPropertyViewSet(
    viewsets.ModelViewSet
):
    """A viewset for managing bookmarked properties.
    This viewset allows authenticated users to bookmark and unbookmark properties.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.BookmarkPropertySerializer

    def get_queryset(self):
        """Returns a queryset of properties bookmarked by the authenticated user."""
        return models.BookmarkedProperty.objects.filter(
            user=self.request.user,
            property__banned_properties__isnull=True,
            property__is_active=True,
            property__is_deleted=False
        )

    def perform_create(self, serializer):
        """Handles the creation of a bookmarked property."""
        serializer.save(user=self.request.user)

    # delete by property ID action
    @extend_schema(
        operation_id='Unbookmark Property',
        description='Unbookmark a property for the authenticated user.',
        responses={204: 'No Content'}
    )
    @action(methods=['delete'], detail=False, url_path='by-property-id/(?P<property_id>[^/.]+)', url_name='unbookmark')
    def unbookmark(self, request, property_id=None):
        """Unbookmarks a property for the authenticated user."""
        try:
            property = models.Property.objects.get(id=property_id)
            bookmark = models.BookmarkedProperty.objects.filter(
                user=request.user,
                property=property
            )
            bookmark.delete()
            return Response(status=204)
        except models.Property.DoesNotExist:
            return Response({"detail": "Property not found."}, status=404)
        except models.BookmarkedProperty.DoesNotExist:
            return Response({"detail": "Property not bookmarked by user."}, status=400)


class HostApartmentPropertyViewSet(
    viewsets.ModelViewSet
):
    """
    A viewset for managing properties hosted by a user.
    This viewset allows users to view and manage properties they host.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ApartmentPropertySerializer
    parser_classes = [parsers.MultiPartParser]

    def get_queryset(self):
        """Returns a queryset of properties hosted by the authenticated user."""
        if self.request.user.is_stakeholder():
            return models.ApartmentProperty.objects.filter(
                listed_by=self.request.user.stakeholder_account,
                is_deleted=False,
            )
        return models.Property.objects.none()

    def perform_destroy(self, instance):
        """Handles the deletion of a hosted property."""
        if instance.listed_by == self.request.user.stakeholder_account:
            instance.is_deleted = True
            instance.save()
        else:
            raise PermissionError(
                "You do not have permission to delete this property.")
    
    def create(self, request: Request, *args, **kwargs):
        images = {} # files that starts with 'image__' in data list
        # Create a mutable copy of request.data
        mutable_data = request.data.copy()
        for key, value in request.data.items():
            if key.startswith('image__'):
                print(f"Processing image: {key}", value, type(value))
                if value and isinstance(value, InMemoryUploadedFile):
                    _, lookup = key.split('__')
                    print(f"Adding image: {key}")
                    images[lookup] = value
                mutable_data.pop(key, None) # Remove the image data from data
        # Save the property first
        serializer = self.get_serializer(data=mutable_data)
        serializer.is_valid(raise_exception=True)
        # Pass the listed_by field from the request user's stakeholder account
        property_instance = serializer.save(listed_by=self.request.user.stakeholder_account)
        # Save the images
        for lookup, image in images.items():
            models.PropertyImage.objects.create(
                property=property_instance, 
                image=image,
                is_primary=(lookup == '0')  # Set first image as primary
            )
        # Return the serialized property instance
        return Response(
            self.get_serializer(property_instance).data,
            status=201
        )
    
    def update(self, request: Request, *args, **kwargs):
        images = {}  # files that starts with 'image__' in data list
        # Create a mutable copy of request.data
        mutable_data = request.data.copy()
        for key, value in request.data.items():
            if key.startswith('image__'):
                print(f"Processing image: {key}", value, type(value))
                if value and isinstance(value, InMemoryUploadedFile):
                    _, lookup = key.split('__')
                    print(f"Adding image: {key}")
                    images[lookup] = value
                mutable_data.pop(key, None)  # Remove the image data from request data
        # Update the property first
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=mutable_data)
        serializer.is_valid(raise_exception=True)
        property_instance = serializer.save()
        # Save the images
        for lookup, image in images.items():
            models.PropertyImage.objects.create(
                property=property_instance,
                image=image,
                is_primary=(lookup == '0')  # Set first image as primary
            )
        # Return the serialized property instance
        return Response(
            self.get_serializer(property_instance).data,
            status=200
        )
    
    def partial_update(self, request: Request, *args, **kwargs):
        images = {}  # files that starts with 'image__' in data list
        # Create a mutable copy of request.data
        mutable_data = request.data.copy()
        for key, value in request.data.items():
            if key.startswith('image__'):
                print(f"Processing image: {key}", value, type(value))
                if value and isinstance(value, InMemoryUploadedFile):
                    _, lookup = key.split('__')
                    print(f"Adding image: {key}")
                    images[lookup] = value
                mutable_data.pop(key, None)  # Remove the image data from data
        # Update the property first
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=mutable_data, partial=True)
        serializer.is_valid(raise_exception=True)
        property_instance = serializer.save()
        # Save the images
        for lookup, image in images.items():
            models.PropertyImage.objects.create(
                property=property_instance,
                image=image,
                is_primary=(lookup == '0')  # Set first image as primary
            )
        # Return the serialized property instance
        return Response(
            self.get_serializer(property_instance).data,
            status=200
        )


class HostHomePropertyViewSet(
    viewsets.ModelViewSet
):
    """
    A viewset for managing home properties hosted by a user.
    This viewset allows users to view and manage home properties they host.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.HomePropertySerializer
    parser_classes = [parsers.MultiPartParser]

    def get_queryset(self):
        """Returns a queryset of home properties hosted by the authenticated user."""
        if self.request.user.is_stakeholder():
            return models.HomeProperty.objects.filter(
                listed_by=self.request.user.stakeholder_account,
                is_deleted=False,
            )
        return models.Property.objects.none()

    def perform_destroy(self, instance):
        """Handles the deletion of a hosted home property."""
        if instance.listed_by == self.request.user.stakeholder_account:
            instance.is_deleted = True
            instance.save()
        else:
            raise PermissionError(
                "You do not have permission to delete this property.")
    
    def create(self, request, *args, **kwargs):
        images = {} # files that starts with 'image__' in data list
        bedrooms = {}
        # Create a mutable copy of request.data
        mutable_data = request.data.copy()
        for key, value in request.data.items():
            if key.startswith('image__'):
                print(f"Processing image: {key}", value, type(value))
                if value and isinstance(value, InMemoryUploadedFile):
                    _, lookup = key.split('__')
                    print(f"Adding image: {key}")
                    images[lookup] = value
                mutable_data.pop(key, None)
            elif key.startswith('bedroom__'):
                if value and value != 'null':
                    _, lookup, field = key.split('__')
                    if lookup not in bedrooms:
                        bedrooms[lookup] = {}
                    bedrooms[lookup][field] = value
                mutable_data.pop(key, None)  # Remove the bedroom data from request data
        # Save the property first
        serializer = self.get_serializer(data=mutable_data)
        serializer.is_valid(raise_exception=True)
        # Pass the listed_by field from the request user's stakeholder account
        property_instance = serializer.save(listed_by=self.request.user.stakeholder_account)
        # Save the images
        for lookup, image in images.items():
            models.PropertyImage.objects.create(
                property=property_instance, image=image, is_primary= (lookup == '0'))
        # Save the bedrooms
        for lookup, bedroom_data in bedrooms.items():
            models.HomePropertyBedroom.objects.create(
                home_property=property_instance,
                **bedroom_data
            )
        # Return the serialized property instance
        return Response(
            self.get_serializer(property_instance).data,
            status=201
        )
    
    def update(self, request, *args, **kwargs):
        images = {}  # files that starts with 'image__' in data list
        bedrooms = {}
        # Create a mutable copy of request.data
        mutable_data = request.data.copy()
        for key, value in request.data.items():
            if key.startswith('image__'):
                print(f"Processing image: {key}", value, type(value))
                if value and isinstance(value, InMemoryUploadedFile):
                    _, lookup = key.split('__')
                    print(f"Adding image: {key}")
                    images[lookup] = value
                mutable_data.pop(key, None)  # Remove the image data from data
            elif key.startswith('bedroom__'):
                if value and value != 'null':
                    _, lookup, field = key.split('__')
                    if lookup not in bedrooms:
                        bedrooms[lookup] = {}
                    bedrooms[lookup][field] = value
                mutable_data.pop(key, None)  # Remove the bedroom data from request data
        # Update the property first
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=mutable_data)
        serializer.is_valid(raise_exception=True)
        property_instance = serializer.save()
        # Save the images
        for lookup, image in images.items():
            models.PropertyImage.objects.create(
                property=property_instance, 
                image=image,
                is_primary=(lookup == '0')  # Set first image as primary
            )
        # Save the bedrooms
        for lookup, bedroom_data in bedrooms.items():
            if bedroom_data['level'] and bedroom_data['dimention_width'] and bedroom_data['dimention_length']:
                if bedroom_data.get('id'):
                    # Update existing bedroom
                    models.HomePropertyBedroom.objects.filter(id=bedroom_data['id']).update(
                        home_property=property_instance,
                        **bedroom_data
                    )
                else:
                    # Create new bedroom
                    if 'id' in bedroom_data:
                        del bedroom_data['id']  # Remove id if present to avoid conflicts
                    models.HomePropertyBedroom.objects.create(
                        home_property=property_instance,
                        **bedroom_data
                    )
        # Return the serialized property instance
        return Response(
            self.get_serializer(property_instance).data,
            status=200
        )
    
    def partial_update(self, request, *args, **kwargs):
        images = {}  # files that starts with 'image__' in data list
        bedrooms = {}
        # Create a mutable copy of request.data
        mutable_data = request.data.copy()
        print("Request data:", mutable_data)
        for key, value in request.data.items():
            if key.startswith('image__'):
                print(f"Processing image: {key}", value, type(value))
                if value and isinstance(value, InMemoryUploadedFile):
                    _, lookup = key.split('__')
                    print(f"Adding image: {key}")
                    images[lookup] = value
                mutable_data.pop(key, None)  # Remove the image data from request data
            elif key.startswith('bedroom__'):
                if value and value != 'null':
                    _, lookup, field = key.split('__')
                    if lookup not in bedrooms:
                        bedrooms[lookup] = {}
                    bedrooms[lookup][field] = value
                mutable_data.pop(key, None)  # Remove the bedroom data from request data
        # Update the property first
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=mutable_data, partial=True)
        serializer.is_valid(raise_exception=True)
        property_instance = serializer.save()
        # Save the images
        for lookup, image in images.items():
            models.PropertyImage.objects.create(
                property=property_instance,
                image=image,
                is_primary=(lookup == '0')  # Set first image as primary
            )
        # Save the bedrooms
        for lookup, bedroom_data in bedrooms.items():
            if bedroom_data['level'] and bedroom_data['dimention_width'] and bedroom_data['dimention_length']:
                if bedroom_data.get('id'):
                    # Update existing bedroom
                    models.HomePropertyBedroom.objects.filter(id=bedroom_data['id']).update(
                        home_property=property_instance,
                        **bedroom_data
                    )
                else:
                    # Create new bedroom
                    if 'id' in bedroom_data:
                        del bedroom_data['id']  # Remove id if present to avoid conflicts
                    models.HomePropertyBedroom.objects.create(
                        home_property=property_instance,
                        **bedroom_data
                    )
        # Return the serialized property instance
        return Response(
            self.get_serializer(property_instance).data,
            status=200
        )


class HostPropertyImageViewSet(
    # viewsets.generics.CreateAPIView,
    viewsets.mixins.UpdateModelMixin,
    viewsets.mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    A viewset for managing images of properties hosted by a user.
    This viewset allows users to upload and manage images for their properties.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.HostPropertyImageSerializer
    parser_classes = [parsers.MultiPartParser]

    def get_queryset(self):
        """Returns a queryset of images for properties hosted by the authenticated user."""
        if self.request.user.is_stakeholder():
            return models.PropertyImage.objects.filter(
                property__listed_by=self.request.user.stakeholder_account,
            )
        return models.PropertyImage.objects.none()


class HostHomePropertyBedroomViewSet(
    # viewsets.mixins.CreateModelMixin,
    viewsets.mixins.UpdateModelMixin,
    viewsets.mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    A viewset for managing bedrooms of home properties hosted by a user.
    This viewset allows users to upload and manage bedrooms for their home properties.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.HomePropertyBedroomSerializer

    def get_queryset(self):
        """Returns a queryset of bedrooms for home properties hosted by the authenticated user."""
        if self.request.user.is_stakeholder():
            return models.HomePropertyBedroom.objects.filter(
                home_property__listed_by=self.request.user.stakeholder_account,
            )
        return models.HomePropertyBedroom.objects.none()


class PropertyFieldChoicesView(
    APIView
):
    """
    A viewset for providing choices for property fields.
    This viewset allows users to retrieve choices for property-related fields.
    """

    @extend_schema(
        operation_id='Get Property Choices',
        description='Retrieve choices for property-related fields.',
        responses={200: {}}
    )
    def get(self, request, *args, **kwargs):
        """
        Returns a list of choices for property-related fields.
        """
        choices = {
            'LEVEL_CHOICES': models.LEVEL_CHOICES,
            'PROPERTY_TYPE_CHOICES': models.Property.PROPERTY_TYPE_CHOICES,
            'LISTING_TYPE_CHOICES': models.HomeProperty.LISTING_TYPE_CHOICES,
            'PARKING_FEATURE_CHOICES': models.HomeProperty.PARKING_FEATURE_CHOICES,
            # HOME_TYPE_CHOICES
            'HOME_TYPE_CHOICES': models.HomeProperty.HOME_TYPE_CHOICES,
            # ARCHITECTURAL_STYLE_CHOICES
            'ARCHITECTURAL_STYLE_CHOICES': models.HomeProperty.ARCHITECTURAL_STYLE_CHOICES,
            # PROPERTY_CONDITION_CHOICES
            'PROPERTY_CONDITION_CHOICES': models.HomeProperty.PROPERTY_CONDITION_CHOICES,
            # APARTMENT_TYPE_CHOICES
            'APARTMENT_TYPE_CHOICES': models.ApartmentProperty.APARTMENT_TYPE_CHOICES,
        }
        return Response(choices, status=200)


class InterestedPropertyViewSet(
    viewsets.ModelViewSet
):
    """A viewset for managing interested properties.
    This viewset allows authenticated users to express interest in properties.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.InterestedPropertySerializer

    def get_serializer(self, *args, **kwargs):
        request = self.request
        kwargs['context'] = {'request': request}
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        """Returns a queryset of properties the authenticated user is interested in."""
        return models.InterestedProperty.objects.filter(
            user=self.request.user,
            property__banned_properties__isnull=True,
            property__is_active=True,
            property__is_deleted=False
        )

    def perform_create(self, serializer):
        """Handles the creation of an interested property."""
        inst = serializer.save(user=self.request.user)
        # Create the first dialog
        models.InterestedPropertyDialog.objects.create(
            interested_property=inst,
            message="I am interested in this property.",
            sender=self.request.user
        )
    
    # Action to get websocket URL for all interested properties interactions
    @extend_schema(
        operation_id='Get Interested Properties WebSocket URL',
        description='Retrieve the WebSocket URL for interested properties interactions.',
        responses={200: {'type': 'object', 'properties': {'websocket_url': {'type': 'string'}}}}
    )
    @action(methods=['get'], detail=False, url_path='websocket-url', url_name='websocket-url')
    def websocket_url(self, request):
        """Returns the WebSocket URL for interested properties interactions."""
        ws_scheme = 'wss' if request.is_secure() else 'ws'
        host = request.get_host()
        
        # Create and encrypt the payload
        payload = {
            'user_id': str(request.user.id),
            "timestamp": str(timezone.now().timestamp())
        }
        encrypted_payload = encrypt_payload(payload)
        
        websocket_url = f"{ws_scheme}://{host}/ws/chat/{encrypted_payload}/"
        return Response({'websocket_url': websocket_url}, status=200)