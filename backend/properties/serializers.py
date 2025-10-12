from rest_framework import serializers
from accounts.models import HostAccount
from . import models


class PropertyImageSerializer(serializers.ModelSerializer):
    """
    Serializer for PropertyImage model.
    It includes fields for the image and the property it belongs to.
    """

    class Meta:
        model = models.PropertyImage
        fields = ['id', 'image', 'is_primary']
        read_only_fields = ['id']


class CommercialPropertyRoomSerializer(serializers.ModelSerializer):
    """
    Serializer for CommercialPropertyRoom model.
    It includes fields for the room details and calculates the area.
    """
    area = serializers.CharField(read_only=True)

    class Meta:
        model = models.CommercialPropertyRoom
        exclude = ['property']
        read_only_fields = ['id']


class CommercialPropertyListedBySerializer(serializers.ModelSerializer):
    """
    Serializer for CommercialPropertyListedBy model.
    It includes fields for the user who listed the property.
    """
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    class Meta:
        model = HostAccount
        fields = ['id', 'full_name', 'is_verified', 'host_photo', 'created_at', 'updated_at']
        read_only_fields = ['id', 'full_name', 'is_verified', 'created_at', 'updated_at']


class VerifiedPropertySerializer(serializers.ModelSerializer):
    """
    Serializer for VerifiedProperty model.
    It includes fields for the verification details.
    """
    class Meta:
        model = models.VerifiedProperty
        fields = ['id', 'verification_phase', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class BannedPropertySerializer(serializers.ModelSerializer):
    """
    Serializer for BannedProperty model.
    It includes fields for the ban details.
    """
    class Meta:
        model = models.BannedProperty
        fields = ['id', 'reason', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CommercialPropertySerializer(serializers.ModelSerializer):
    """
    Serializer for CommercialProperty model.
    It includes fields for the property and its images.
    """
    is_verified = serializers.BooleanField(read_only=True)
    verified = VerifiedPropertySerializer(read_only=True)
    is_banned = serializers.BooleanField(read_only=True)
    banned = BannedPropertySerializer(read_only=True)
    rooms = CommercialPropertyRoomSerializer(many=True, read_only=True)
    images = PropertyImageSerializer(many=True, required=False, allow_null=True, read_only=True)
    listed_by = CommercialPropertyListedBySerializer(read_only=True)
    finished_area = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    total_rooms = serializers.IntegerField(read_only=True)
    is_bookmarked = serializers.SerializerMethodField()
    title = serializers.CharField(read_only=True)
    subtitle = serializers.CharField(read_only=True)
    tag = serializers.CharField(read_only=True)
    features = serializers.CharField(read_only=True)
    amenities = serializers.CharField(read_only=True)
    primary_image = serializers.ImageField(read_only=True)
    image__1__is_primary = serializers.BooleanField(write_only=True, required=False)
    image__1__image = serializers.ImageField(write_only=True, required=False, allow_null=True)
    room__1__area = serializers.CharField(write_only=True, required=False)
    room__1__level = serializers.CharField(write_only=True, required=False)
    room__1__dimention_width = serializers.DecimalField(
        write_only=True, required=False, max_digits=10, decimal_places=2)
    room__1__dimention_length = serializers.DecimalField(
        write_only=True, required=False, max_digits=10, decimal_places=2)

    class Meta:
        model = models.CommercialProperty
        fields = '__all__'
        read_only_fields = ['id', 'last_checked', 'property_type', 'listed_by']
    
    def create(self, validated_data):
        # Recursively remove nested data before creating the CommercialProperty instance
        for key in list(validated_data.keys()):
            if key.startswith('image__') or key.startswith('room__'):
                validated_data.pop(key)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Recursively remove nested data before updating the CommercialProperty instance
        for key in list(validated_data.keys()):
            if key.startswith('image__') or key.startswith('room__'):
                validated_data.pop(key)
        return super().update(instance, validated_data)
    
    def get_is_bookmarked(self, obj):
        """
        Check if the property is bookmarked by the current user.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_bookmarked(request.user)
        return False


class ShortletPropertySerializer(serializers.ModelSerializer):
    """
    Serializer for ShortletProperty model.
    It includes fields for the property and its images.
    """
    is_verified = serializers.BooleanField(read_only=True)
    verified = VerifiedPropertySerializer(read_only=True)
    is_banned = serializers.BooleanField(read_only=True)
    banned = BannedPropertySerializer(read_only=True)
    images = PropertyImageSerializer(many=True, required=False, allow_null=True, read_only=True)
    listed_by = CommercialPropertyListedBySerializer(read_only=True)
    is_bookmarked = serializers.SerializerMethodField(read_only=True)
    title = serializers.CharField(read_only=True)
    subtitle = serializers.CharField(read_only=True)
    tag = serializers.CharField(read_only=True)
    features = serializers.CharField(read_only=True)
    amenities = serializers.CharField(read_only=True)
    primary_image = serializers.ImageField(read_only=True)
    image__1__is_primary = serializers.BooleanField(write_only=True, required=False)
    image__1__image = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = models.ShortletProperty
        fields = '__all__'
        read_only_fields = ['id', 'last_checked', 'property_type', 'listed_by']
    
    def create(self, validated_data):
        # Recursively remove nested data before creating the ShortletProperty instance
        for key in list(validated_data.keys()):
            if key.startswith('image__'):
                validated_data.pop(key)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Recursively remove nested data before updating the ShortletProperty instance
        for key in list(validated_data.keys()):
            if key.startswith('image__'):
                validated_data.pop(key)
        return super().update(instance, validated_data)
    
    def get_is_bookmarked(self, obj):
        """
        Check if the property is bookmarked by the current user.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_bookmarked(request.user)
        return False


class PropertySerializer(serializers.ModelSerializer):
    """
    Serializer for Property model.
    It includes fields for all the properties and nested serializers for related models.
    """
    commercialproperty = CommercialPropertySerializer(
        required=False, allow_null=True, read_only=True)
    shortletproperty = ShortletPropertySerializer(
        required=False, allow_null=True, read_only=True)
    price = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    subtitle = serializers.CharField(read_only=True)
    tag = serializers.CharField(read_only=True)
    features = serializers.CharField(read_only=True)
    amenities = serializers.CharField(read_only=True)
    primary_image = serializers.ImageField(read_only=True)

    class Meta:
        model = models.Property
        fields = ['id', 'price', 'title', 'subtitle', 'tag', 'features', 'amenities', 'primary_image',
                  'property_type', 'commercialproperty', 'shortletproperty']



class PropertyWithSimilarSerializer(serializers.Serializer):
    """
    Serializer for Property with similar properties.
    It includes the property details and a list of similar properties.
    """

    property = PropertySerializer()
    similar_properties = PropertySerializer(many=True, read_only=True)

    class Meta:
        fields = ['property', 'similar_properties']
        read_only_fields = ['similar_properties']


class BookmarkPropertySerializer(serializers.ModelSerializer):
    """
    Serializer for bookmarking a property.
    It includes the property ID and the user who bookmarked it.
    """
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    property_obj = PropertySerializer(read_only=True, source='property')

    class Meta:
        model = models.BookmarkedProperty
        fields = ['id', 'property', 'user', 'created_at', 'property_obj']
        read_only_fields = ['id', 'user', 'created_at', 'property_obj']


class HostPropertyImageSerializer(serializers.ModelSerializer):
    """
    Serializer for images of properties hosted by a host.
    It includes fields for the image and the property it belongs to.
    """
    class Meta:
        model = models.PropertyImage
        fields = '__all__'
        read_only_fields = ['id']


class MinimalPropertySerializer(serializers.ModelSerializer):
    """
    Minimal serializer for Property model.
    It includes only the essential fields.
    """
    subtitle = serializers.CharField(read_only=True)
    price = serializers.CharField(read_only=True)
    primary_image = serializers.ImageField(read_only=True)
    class Meta:
        model = models.Property
        fields = ['id', 'title', 'subtitle', 'description', 
                  'price', 'primary_image', 'created_at', 'updated_at']
        read_only_fields = ['id']


# models.InterestedPropertyDialog
class InterestedPropertyDialogSerializer(serializers.ModelSerializer):
    """
    Serializer for InterestedPropertyDialog model.
    It includes fields for the dialog and its messages.
    """

    class Meta:
        model = models.InterestedPropertyDialog
        fields = ['id', 'interested_property_id', 'message', 'sender', 'created_at']
        read_only_fields = ['id', 'created_at']

class InterestedPropertySerializer(serializers.ModelSerializer):
    """
    Serializer for InterestedProperty model.
    It includes fields for the interested property and the user who expressed interest.
    """
    property = PropertySerializer(read_only=True)
    dialogs = InterestedPropertyDialogSerializer(read_only=True, many=True)

    class Meta:
        model = models.InterestedProperty
        fields = ['id', 'property_id', 'property', 'user', 'responder', 'created_at', 'dialogs']
        read_only_fields = ['id', 'user', 'responder', 'created_at', 'property', 'dialogs']