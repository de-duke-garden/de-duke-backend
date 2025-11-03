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
            Q(banned__isnull=True) &
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
            Q(banned__isnull=True) &
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
            property__banned__isnull=True,
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


class HostShortletPropertyViewSet(
    viewsets.ModelViewSet
):
    """
    A viewset for managing properties hosted by a user.
    This viewset allows users to view and manage properties they host.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ShortletPropertySerializer
    parser_classes = [parsers.MultiPartParser]

    def get_queryset(self):
        """Returns a queryset of properties hosted by the authenticated user."""
        if self.request.user.is_host():
            return models.ShortletProperty.objects.filter(
                listed_by=self.request.user.host_account,
                is_deleted=False,
            )
        return models.Property.objects.none()

    def perform_destroy(self, instance):
        """Handles the deletion of a hosted property."""
        if instance.listed_by == self.request.user.host_account:
            instance.is_deleted = True
            instance.save()
        else:
            raise PermissionError(
                "You do not have permission to delete this property.")
    
    def create(self, request: Request, *args, **kwargs):
        images = {} # files that starts with 'image__' in data list
        # Create a mutable copy of request.data
        mutable_data = {}
        for key, value in request.data.items():
            # if key.startswith('image__'):
            #     print(f"Processing image: {key}", value, type(value))
            #     if value and isinstance(value, InMemoryUploadedFile):
            #         _, lookup = key.split('__')
            #         print(f"Adding image: {key}")
            #         images[lookup] = value
            #     mutable_data.pop(key, None) # Remove the image data from data
            if key.startswith('image__'):
                print(f"Processing image: {key}", value, type(value))
                if value and value != 'null':
                    _, lookup, field = key.split('__')
                    print(f"Adding image: {key}")
                    if lookup not in images:
                        images[lookup] = {}
                    val = value
                    if value == 'true':
                        val = True
                    elif value == 'false':
                        val = False
                    images[lookup][field] = val
            else:
                mutable_data[key] = value
        # Save the property first
        serializer = self.get_serializer(data=mutable_data)
        serializer.is_valid(raise_exception=True)
        # Pass the listed_by field from the request user's host account
        property_instance = serializer.save(listed_by=self.request.user.host_account)
        print("Created property:", property_instance)
        # Save the images
        # for lookup, image in images.items():
        #     models.PropertyImage.objects.create(
        #         property=property_instance, 
        #         image=image,
        #         is_primary=(lookup == '0')  # Set first image as primary
        #     )
        for lookup, image_data in images.items():
            print(f"Image data for {lookup}: {image_data}")
            if image_data.get('is_primary') == True:
                # If this image is marked as primary, unset other primary images
                models.PropertyImage.objects.filter(
                    property=property_instance,
                    is_primary=True
                ).update(is_primary=False)
            models.PropertyImage.objects.create(
                property=property_instance, **image_data,)
        # Return the serialized property instance
        return Response(
            self.get_serializer(property_instance).data,
            status=201
        )
    
    def update(self, request: Request, *args, **kwargs):
        images = {}  # files that starts with 'image__' in data list
        # Create a mutable copy of request.data
        mutable_data = {}
        for key, value in request.data.items():
            # if key.startswith('image__'):
            #     print(f"Processing image: {key}", value, type(value))
            #     if value and isinstance(value, InMemoryUploadedFile):
            #         _, lookup = key.split('__')
            #         print(f"Adding image: {key}")
            #         images[lookup] = value
            #     mutable_data.pop(key, None)  # Remove the image data from request data
            if key.startswith('image__'):
                print(f"Processing image: {key}", value, type(value))
                if value and value != 'null':
                    _, lookup, field = key.split('__')
                    print(f"Adding image: {key}")
                    if lookup not in images:
                        images[lookup] = {}
                    val = value
                    if value == 'true':
                        val = True
                    elif value == 'false':
                        val = False
                    images[lookup][field] = val
            else:
                mutable_data[key] = value
        # Update the property first
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=mutable_data)
        serializer.is_valid(raise_exception=True)
        property_instance = serializer.save()
        # Save the images
        # for lookup, image in images.items():
        #     models.PropertyImage.objects.create(
        #         property=property_instance,
        #         image=image,
        #         is_primary=(lookup == '0')  # Set first image as primary
        #     )
        for lookup, image_data in images.items():
            if image_data.get('is_primary') == True:
                # If this image is marked as primary, unset other primary images
                models.PropertyImage.objects.filter(
                    property=property_instance,
                    is_primary=True
                ).update(is_primary=False)
            models.PropertyImage.objects.create(
                property=property_instance, **image_data,)
        # Return the serialized property instance
        return Response(
            self.get_serializer(property_instance).data,
            status=200
        )
    
    def partial_update(self, request: Request, *args, **kwargs):
        images = {}  # files that starts with 'image__' in data list
        # Create a mutable copy of request.data
        mutable_data = {}
        for key, value in request.data.items():
            # if key.startswith('image__'):
            #     print(f"Processing image: {key}", value, type(value))
            #     if value and isinstance(value, InMemoryUploadedFile):
            #         _, lookup = key.split('__')
            #         print(f"Adding image: {key}")
            #         images[lookup] = value
            #     mutable_data.pop(key, None)  # Remove the image data from data
            if key.startswith('image__'):
                print(f"Processing image: {key}", value, type(value))
                if value and value != 'null':
                    _, lookup, field = key.split('__')
                    print(f"Adding image: {key}")
                    if lookup not in images:
                        images[lookup] = {}
                    val = value
                    if value == 'true':
                        val = True
                    elif value == 'false':
                        val = False
                    images[lookup][field] = val
            else:
                mutable_data[key] = value
        # Update the property first
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=mutable_data, partial=True)
        serializer.is_valid(raise_exception=True)
        property_instance = serializer.save()
        # Save the images
        # for lookup, image in images.items():
        #     models.PropertyImage.objects.create(
        #         property=property_instance,
        #         image=image,
        #         is_primary=(lookup == '0')  # Set first image as primary
        #     )
        for lookup, image_data in images.items():
            print(f"Image data for {lookup}: {image_data}")
            if image_data.get('is_primary') == True:
                # If this image is marked as primary, unset other primary images
                models.PropertyImage.objects.filter(
                    property=property_instance,
                    is_primary=True
                ).update(is_primary=False)
            models.PropertyImage.objects.create(
                property=property_instance, **image_data,)
        # Return the serialized property instance
        return Response(
            self.get_serializer(property_instance).data,
            status=200
        )


class HostCommercialPropertyViewSet(
    viewsets.ModelViewSet
):
    """
    A viewset for managing commercial properties hosted by a user.
    This viewset allows users to view and manage commercial properties they host.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.CommercialPropertySerializer
    parser_classes = [parsers.MultiPartParser]

    def get_queryset(self):
        """Returns a queryset of commercial properties hosted by the authenticated user."""
        if self.request.user.is_host():
            return models.CommercialProperty.objects.filter(
                listed_by=self.request.user.host_account,
                is_deleted=False,
            )
        return models.Property.objects.none()

    def perform_destroy(self, instance):
        """Handles the deletion of a hosted commercial property."""
        if instance.listed_by == self.request.user.host_account:
            instance.is_deleted = True
            instance.save()
        else:
            raise PermissionError(
                "You do not have permission to delete this property.")
    
    def create(self, request, *args, **kwargs):
        images = {} # files that starts with 'image__' in data list
        rooms = {}
        # Create a mutable copy of request.data
        mutable_data = {}
        for key, value in request.data.items():
            if key.startswith('image__'):
                print(f"Processing image: {key}", value, type(value))
                if value and value != 'null':
                    _, lookup, field = key.split('__')
                    print(f"Adding image: {key}")
                    if lookup not in images:
                        images[lookup] = {}
                    val = value
                    if value == 'true':
                        val = True
                    elif value == 'false':
                        val = False
                    images[lookup][field] = val
            elif key.startswith('room__'):
                if value and value != 'null':
                    _, lookup, field = key.split('__')
                    if lookup not in rooms:
                        rooms[lookup] = {}
                    rooms[lookup][field] = value
            else:
                mutable_data[key] = value
        # Save the property first
        print("Mutable data for property creation:", mutable_data)
        serializer = self.get_serializer(data=mutable_data)
        serializer.is_valid(raise_exception=True)
        # Pass the listed_by field from the request user's host account
        property_instance = serializer.save(listed_by=self.request.user.host_account)
        # Save the images
        for lookup, image_data in images.items():
            if image_data.get('is_primary') == True:
                # If this image is marked as primary, unset other primary images
                models.PropertyImage.objects.filter(
                    property=property_instance,
                    is_primary=True
                ).update(is_primary=False)
            models.PropertyImage.objects.create(
                property=property_instance, **image_data,)
        # Save the rooms
        for lookup, room_data in rooms.items():
            models.CommercialPropertyRoom.objects.create(
                property=property_instance,
                **room_data
            )
        # Return the serialized property instance
        return Response(
            self.get_serializer(property_instance).data,
            status=201
        )
    
    def update(self, request, *args, **kwargs):
        images = {}  # files that starts with 'image__' in data list
        rooms = {}
        # Create a mutable copy of request.data
        mutable_data = {}
        for key, value in request.data.items():
            # if key.startswith('image__'):
            #     print(f"Processing image: {key}", value, type(value))
            #     if value and isinstance(value, InMemoryUploadedFile):
            #         _, lookup = key.split('__')
            #         print(f"Adding image: {key}")
            #         images[lookup] = value
            #     mutable_data.pop(key, None)  # Remove the image data from data
            if key.startswith('image__'):
                print(f"Processing image: {key}", value, type(value))
                if value and value != 'null':
                    _, lookup, field = key.split('__')
                    print(f"Adding image: {key}")
                    if lookup not in images:
                        images[lookup] = {}
                    val = value
                    if value == 'true':
                        val = True
                    elif value == 'false':
                        val = False
                    images[lookup][field] = val
            elif key.startswith('room__'):
                if value and value != 'null':
                    _, lookup, field = key.split('__')
                    if lookup not in rooms:
                        rooms[lookup] = {}
                    rooms[lookup][field] = value
            else:
                mutable_data[key] = value
        # Update the property first
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=mutable_data)
        serializer.is_valid(raise_exception=True)
        property_instance = serializer.save()
        # Save the images
        # for lookup, image in images.items():
        #     models.PropertyImage.objects.create(
        #         property=property_instance, 
        #         image=image,
        #         is_primary=(lookup == '0')  # Set first image as primary
        #     )
        for lookup, image_data in images.items():
            if image_data.get('is_primary') == True:
                # If this image is marked as primary, unset other primary images
                models.PropertyImage.objects.filter(
                    property=property_instance,
                    is_primary=True
                ).update(is_primary=False)
            models.PropertyImage.objects.create(
                property=property_instance, **image_data,)
        # Save the rooms
        for lookup, room_data in rooms.items():
            if room_data['level'] and room_data['dimention_width'] and room_data['dimention_length']:
                if room_data.get('id'):
                    # Update existing room
                    models.CommercialPropertyRoom.objects.filter(id=room_data['id']).update(
                        property=property_instance,
                        **room_data
                    )
                else:
                    # Create new room
                    if 'id' in room_data:
                        del room_data['id']  # Remove id if present to avoid conflicts
                    models.CommercialPropertyRoom.objects.create(
                        property=property_instance,
                        **room_data
                    )
        # Return the serialized property instance
        return Response(
            self.get_serializer(property_instance).data,
            status=200
        )
    
    def partial_update(self, request, *args, **kwargs):
        images = {}  # files that starts with 'image__' in data list
        rooms = {}
        # Create a mutable copy of request.data
        mutable_data = {}
        print("Request data:", mutable_data)
        for key, value in request.data.items():
            # if key.startswith('image__'):
            #     print(f"Processing image: {key}", value, type(value))
            #     if value and isinstance(value, InMemoryUploadedFile):
            #         _, lookup = key.split('__')
            #         print(f"Adding image: {key}")
            #         images[lookup] = value
            #     mutable_data.pop(key, None)  # Remove the image data from request data
            if key.startswith('image__'):
                print(f"Processing image: {key}", value, type(value))
                if value and value != 'null':
                    _, lookup, field = key.split('__')
                    print(f"Adding image: {key}")
                    if lookup not in images:
                        images[lookup] = {}
                    val = value
                    if value == 'true':
                        val = True
                    elif value == 'false':
                        val = False
                    images[lookup][field] = val
            elif key.startswith('room__'):
                if value and value != 'null':
                    _, lookup, field = key.split('__')
                    if lookup not in rooms:
                        rooms[lookup] = {}
                    rooms[lookup][field] = value
            else:
                mutable_data[key] = value
        # Update the property first
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=mutable_data, partial=True)
        serializer.is_valid(raise_exception=True)
        property_instance = serializer.save()
        # Save the images
        # for lookup, image in images.items():
        #     models.PropertyImage.objects.create(
        #         property=property_instance,
        #         image=image,
        #         is_primary=(lookup == '0')  # Set first image as primary
        #     )
        for lookup, image_data in images.items():
            if image_data.get('is_primary') == True:
                # If this image is marked as primary, unset other primary images
                models.PropertyImage.objects.filter(
                    property=property_instance,
                    is_primary=True
                ).update(is_primary=False)
            models.PropertyImage.objects.create(
                property=property_instance, **image_data,)
        # Save the rooms
        for lookup, room_data in rooms.items():
            if room_data['level'] and room_data['dimention_width'] and room_data['dimention_length']:
                if room_data.get('id'):
                    # Update existing room
                    models.CommercialPropertyRoom.objects.filter(id=room_data['id']).update(
                        property=property_instance,
                        **room_data
                    )
                else:
                    # Create new room
                    if 'id' in room_data:
                        del room_data['id']  # Remove id if present to avoid conflicts
                    models.CommercialPropertyRoom.objects.create(
                        property=property_instance,
                        **room_data
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
        if self.request.user.is_host():
            return models.PropertyImage.objects.filter(
                property__listed_by=self.request.user.host_account,
            )
        return models.PropertyImage.objects.none()


class HostCommercialPropertyRoomViewSet(
    # viewsets.mixins.CreateModelMixin,
    viewsets.mixins.UpdateModelMixin,
    viewsets.mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    A viewset for managing rooms of commercial properties hosted by a user.
    This viewset allows users to upload and manage rooms for their commercial properties.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.CommercialPropertyRoomSerializer

    def get_queryset(self):
        """Returns a queryset of rooms for commercial properties hosted by the authenticated user."""
        if self.request.user.is_host():
            return models.CommercialPropertyRoom.objects.filter(
                property__listed_by=self.request.user.host_account,
            )
        return models.CommercialPropertyRoom.objects.none()


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
            'LISTING_TYPE_CHOICES': models.CommercialProperty.LISTING_TYPE_CHOICES,
            'PARKING_FEATURE_CHOICES': models.CommercialProperty.PARKING_FEATURE_CHOICES,
            # COMMERCIAL_TYPE_CHOICES
            'COMMERCIAL_TYPE_CHOICES': models.CommercialProperty.COMMERCIAL_TYPE_CHOICES,
            # ARCHITECTURAL_STYLE_CHOICES
            'ARCHITECTURAL_STYLE_CHOICES': models.CommercialProperty.ARCHITECTURAL_STYLE_CHOICES,
            # PROPERTY_CONDITION_CHOICES
            'PROPERTY_CONDITION_CHOICES': models.CommercialProperty.PROPERTY_CONDITION_CHOICES,
            # SHORTLET_TYPE_CHOICES
            'SHORTLET_TYPE_CHOICES': models.ShortletProperty.SHORTLET_TYPE_CHOICES,
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
            property__banned__isnull=True,
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
        # ws_scheme = 'wss' if request.is_secure() else 'ws'
        # host = request.get_host()
        # Prefer X-Forwarded-* headers (set by Traefik / reverse proxy) but fall back to Django values
        forwarded_proto = request.headers.get('x-forwarded-proto') or request.META.get('HTTP_X_FORWARDED_PROTO')
        proto = (forwarded_proto.split(',')[0].strip() if forwarded_proto else
                 ('https' if request.is_secure() else 'http'))
        ws_scheme = 'wss' if proto == 'https' else 'ws'

        forwarded_host = request.headers.get('x-forwarded-host') or request.META.get('HTTP_X_FORWARDED_HOST')
        host = (forwarded_host.split(',')[0].strip() if forwarded_host else request.get_host())
        # Some proxies can wrongly forward port 0; strip it if present
        if host.endswith(':0'):
            host = host.rsplit(':', 1)[0]
        
        # Create and encrypt the payload
        payload = {
            'user_id': str(request.user.id),
            "timestamp": str(timezone.now().timestamp())
        }
        encrypted_payload = encrypt_payload(payload)
        
        websocket_url = f"{ws_scheme}://{host}/ws/chat/{encrypted_payload}/"
        return Response({'websocket_url': websocket_url}, status=200)