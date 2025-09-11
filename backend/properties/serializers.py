from rest_framework import serializers
from accounts.models import StakeholderAccount
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


class HomePropertyBedroomSerializer(serializers.ModelSerializer):
    """
    Serializer for HomePropertyBedroom model.
    It includes fields for the bedroom and its associated property.
    """
    area = serializers.CharField(read_only=True)

    class Meta:
        model = models.HomePropertyBedroom
        exclude = ['home_property']
        read_only_fields = ['id']


class HomePropertyListedBySerializer(serializers.ModelSerializer):
    """
    Serializer for HomePropertyListedBy model.
    It includes fields for the user who listed the property.
    """
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    class Meta:
        model = StakeholderAccount
        fields = ['id', 'full_name']
        read_only_fields = ['id', 'full_name']


class HomePropertySerializer(serializers.ModelSerializer):
    """
    Serializer for HomeProperty model.
    It includes fields for the property and its images.
    """
    is_verified = serializers.BooleanField(read_only=True)
    bedrooms = HomePropertyBedroomSerializer(many=True, read_only=True)
    images = PropertyImageSerializer(many=True, required=False, allow_null=True, read_only=True)
    listed_by = HomePropertyListedBySerializer(read_only=True)
    finished_area = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    total_bathrooms = serializers.IntegerField(read_only=True)
    total_bedrooms = serializers.IntegerField(read_only=True)
    is_bookmarked = serializers.SerializerMethodField()
    image__0 = serializers.ImageField(write_only=True, required=False)
    image__1 = serializers.ImageField(write_only=True, required=False)
    image__2 = serializers.ImageField(write_only=True, required=False)
    image__3 = serializers.ImageField(write_only=True, required=False)
    bedroom__0__area = serializers.CharField(write_only=True, required=False)
    bedroom__0__level = serializers.CharField(write_only=True, required=False)
    bedroom__0__dimention_width = serializers.DecimalField(
        write_only=True, required=False, max_digits=10, decimal_places=2)
    bedroom__0__dimention_length = serializers.DecimalField(
        write_only=True, required=False, max_digits=10, decimal_places=2)

    class Meta:
        model = models.HomeProperty
        fields = '__all__'
        read_only_fields = ['id', 'last_checked', 'property_type', 'listed_by']
    

    def get_is_bookmarked(self, obj):
        """
        Check if the property is bookmarked by the current user.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_bookmarked(request.user)
        return False


class ApartmentPropertySerializer(serializers.ModelSerializer):
    """
    Serializer for ApartmentProperty model.
    It includes fields for the property and its images.
    """
    is_verified = serializers.BooleanField(read_only=True)
    images = PropertyImageSerializer(many=True, required=False, allow_null=True, read_only=True)
    listed_by = HomePropertyListedBySerializer(read_only=True)
    is_bookmarked = serializers.SerializerMethodField()
    image__0 = serializers.ImageField(write_only=True, required=False)
    image__1 = serializers.ImageField(write_only=True, required=False)
    image__2 = serializers.ImageField(write_only=True, required=False)
    image__3 = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = models.ApartmentProperty
        fields = '__all__'
        read_only_fields = ['id', 'last_checked', 'property_type', 'listed_by']
    
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
    homeproperty = HomePropertySerializer(
        required=False, allow_null=True, read_only=True)
    apartmentproperty = ApartmentPropertySerializer(
        required=False, allow_null=True, read_only=True)

    class Meta:
        model = models.Property
        fields = ['id', 'property_type', 'homeproperty', 'apartmentproperty',]


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


class HostApartmentPropertySerializer(serializers.ModelSerializer):
    """
    Serializer for properties hosted by a stakeholder.
    It includes fields for the property and its images.
    """
    is_verified = serializers.BooleanField(read_only=True)
    images = PropertyImageSerializer(many=True, read_only=True)

    class Meta:
        model = models.ApartmentProperty
        fields = '__all__'
        read_only_fields = ['id', 'last_checked', 'property_type', 'listed_by']


class HostHomePropertySerializer(serializers.ModelSerializer):
    """
    Serializer for home properties hosted by a stakeholder.
    It includes fields for the property and its images.
    """
    is_verified = serializers.BooleanField(read_only=True)
    images = PropertyImageSerializer(many=True, read_only=True)

    class Meta:
        model = models.HomeProperty
        fields = '__all__'
        read_only_fields = ['id', 'last_checked', 'property_type', 'listed_by']


class HostPropertyImageSerializer(serializers.ModelSerializer):
    """
    Serializer for images of properties hosted by a stakeholder.
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
    subtitle = serializers.SerializerMethodField(read_only=True)
    price = serializers.SerializerMethodField(read_only=True)
    image = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = models.Property
        fields = ['id', 'property_type', 'address', 'description', 'subtitle', 'price', 'image', 'created_at', 'updated_at']
        read_only_fields = ['id', 'property_type']

    def get_subtitle(self, obj):
        """
        Generate a subtitle for the property based on its type and key attributes.
        """
        if obj.property_type == "home":
            home = getattr(obj, 'homeproperty', None)
            if home:
                subtitle = ""
                if home.home_type:
                    subtitle += f"{home.home_type} | "
                if home.architectural_style:
                    subtitle += f"{home.architectural_style} | "
                if home.property_condition:
                    subtitle += f"{home.property_condition} | "
                subtitle += f"{home.total_bedrooms()} Bed, {home.total_bathrooms()} Bath property for {home.list_type.lower()}"
                return subtitle
        elif obj.property_type == "apartment":
            apartment = getattr(obj, 'apartmentproperty', None)
            if apartment:
                subtitle = ""
                if apartment.apartment_type:
                    subtitle += f"{apartment.apartment_type} | "
                if apartment.has_dishwasher:
                    subtitle += f"Dishwasher | "
                if apartment.has_washer:
                    subtitle += f"Washer | "
                if apartment.has_dryer:
                    subtitle += f"Dryer | "
                if apartment.has_oven:
                    subtitle += f"Oven | "
                if apartment.has_refrigerator:
                    subtitle += f"Refrigerator | "
                subtitle += "property for rent"
                return subtitle
        return "Property"
    
    def get_price(self, obj):
        """
        Get the price of the property based on its type.
        """
        if obj.property_type == "home":
            home = getattr(obj, 'homeproperty', None)
            if home:
                return home.price
        elif obj.property_type == "apartment":
            apartment = getattr(obj, 'apartmentproperty', None)
            if apartment:
                return apartment.price
        return None
    
    def get_image(self, obj):
        # Get the primary or first image of the property
        context = self.context
        if obj.images.exists():
            primary_image = obj.images.filter(is_primary=True).first()
            if primary_image:
                return PropertyImageSerializer(primary_image, context=context).data['image']
            return PropertyImageSerializer(obj.images.first(), context=context).data['image']
        return None

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
    property = MinimalPropertySerializer(read_only=True)
    dialogs = InterestedPropertyDialogSerializer(read_only=True, many=True)

    class Meta:
        model = models.InterestedProperty
        fields = ['id', 'property_id', 'property', 'user', 'responder', 'created_at', 'dialogs']
        read_only_fields = ['id', 'user', 'responder', 'created_at', 'property', 'dialogs']