from django.db import models
import uuid
from django.contrib.gis.db.models import PointField
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from accounts.models import StakeholderAccount
import googlemaps
from django.conf import settings
import logging

from utilities.helpers import property_image_upload_handler


logger = logging.getLogger("django")


User = get_user_model()

LEVEL_CHOICES = [
    ("ground", "Ground"),
]

# id, address, location, description, special_tags, is_active, is_deleted, last_checked, created_at, updated_at, listed_by_id, listed_by_user_id, verified_id, verified_user_id
class Property(models.Model):
    """
    Property model class
    """
    PROPERTY_TYPE_CHOICES = [
        ('home', 'Home'),
        ('apartment', 'Apartment'),
        # ('commercial', 'Commercial'),
        # ('land', 'Land'),
        # ('other', 'Other'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    address = models.TextField(null=False, blank=True, help_text="Address of the property (leave blank for reverse geocoding)")
    location = PointField(geography=True, null=False, blank=False)
    description = models.TextField()    
    # special_tags = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    last_checked = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    listed_by = models.ForeignKey(StakeholderAccount, related_name="properties", on_delete=models.CASCADE)
    property_type = models.CharField(max_length=50, blank=True, null=True, choices=PROPERTY_TYPE_CHOICES)

    class Meta:
        verbose_name = "Property"
        verbose_name_plural = "Properties"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Property: {self.address[:100]}..."
    
    def is_banned(self):
        """
        Check if the property is banned.
        """
        return self.banned_properties.exists()
    
    def is_verified(self):
        """
        Check if the property is verified.
        """
        return hasattr(self, 'verified') and self.verified is not None
    
    def is_verified_by(self):
        """
        Check if the property is verified by a user.
        """
        if hasattr(self, 'verified'):
            return self.verified.verified_by
        return None
    
    def save(self, *args, **kwargs):
        """
        Override the save method to reverse geocode the location into an address
        only if the location has changed.
        """
        def _update_address():
            gmaps = googlemaps.Client(key=settings.GOOGLE_MAP_API_KEY)

            # Extract latitude and longitude from the PointField
            latitude = self.location.y
            longitude = self.location.x

            try:
                # Perform reverse geocoding
                result = gmaps.reverse_geocode((latitude, longitude))
                if result:
                    # Extract the formatted address from the response
                    self.address = result[0]['formatted_address']
            except Exception as e:
                # Log the error if reverse geocoding fails
                logger.error(f"Error during reverse geocoding: {e}")

        # Check if the instance already exists in the database
        if self.pk:
            # Fetch the existing instance from the database
            existing_instance = Property.objects.get(pk=self.pk)
            # Compare the current location with the existing location
            if self.location != existing_instance.location:
                _update_address()
        else:
            # For new instances, always perform reverse geocoding
            if self.location:
                _update_address()

        super().save(*args, **kwargs)


# id, image, ads_id, is_primary
class PropertyImage(models.Model):
    """
    PropertyImage model class
    """
    image = models.ImageField(upload_to=property_image_upload_handler)
    property = models.ForeignKey(Property, related_name="images", on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Property Image"
        verbose_name_plural = "Property Images"
        ordering = ["-property__created_at"]

    def __str__(self):
        return f"PropertyImage: {self.property.address[:100]}..."
    
    


# id, list_type, price, has_c_of_o, has_deed_of_assignment, has_power_of_atorney, has_survey_plan, has_governors_consent, total_bathrooms, total_full_bathrooms, laundry_level, has_basement, has_fireplace, total_structure_area, total_interior_livable_area, finished_area_above_ground, finished_area_below_ground, total_parking_spaces, parking_feature, garage_spaces, parel_number, special_conditions, home_type, architectural_style, property_condition, year_built, has_fitness_center, has_game_room, has_bicycle_storage, has_swimming_pool, allow_small_dog, allow_large_dog, allow_cat, property_id, property_listed_by_id, property_listed_by_user_id, property_verified_id, property_verified_user_id
class HomeProperty(Property):
    """
    HomeProperty model class
    """
    LISTING_TYPE_CHOICES = [
        ('sale', 'Sale'),
        ('rent', 'Rent'),
        ('lease', 'Lease'),
    ]

    PARKING_FEATURE_CHOICES = [
        ('attached', 'Attached'),
        ('detached', 'Detached'),
        ('carport', 'Carport'),
        ('street', 'Street'),
    ]

    HOME_TYPE_CHOICES = [
        ('single_family', _('Single Family')),
        ('multi_family', _('Multi Family')),
        ('townhouse', _('Townhouse')),
        ('condo', _('Condo')),
        ('apartment', _('Apartment')),
        ('duplex', _('Duplex')),
        ('triplex', _('Triplex')),
        ('quadruplex', _('Quadruplex')),
        ('mobile_home', _('Mobile Home')),
        ('manufactured_home', _('Manufactured Home')),
        ('modular_home', _('Modular Home')),
        ('vacation_home', _('Vacation Home')),
        ('farm', _('Farm')),
        # ('land', _('Land')),
        ('commercial', _('Commercial')),
        ('industrial', _('Industrial')),
        ('mixed_use', _('Mixed Use')),
        ('other', _('Other')),
    ]

    ARCHITECTURAL_STYLE_CHOICES = [
        ('modern', _('Modern')),
        ('traditional', _('Traditional')),
        ('contemporary', _('Contemporary')),
        ('colonial', _('Colonial')),
        ('craftsman', _('Craftsman')),
        ('ranch', _('Ranch')),
        ('victorian', _('Victorian')),
        ('farmhouse', _('Farmhouse')),
        ('cottage', _('Cottage')),
        ('mediterranean', _('Mediterranean')),
        ('tudor', _('Tudor')),
        ('art_deco', _('Art Deco')),
        ('mid_century_modern', _('Mid-Century Modern')),
        ('industrial', _('Industrial')),
        ('beach', _('Beach')),
        ('mountain', _('Mountain')),
        ('lake', _('Lake')),
        ('desert', _('Desert')),
        ('other', _('Other')),
    ]

    PROPERTY_CONDITION_CHOICES = [
        ('new', _('New')),
        ('like_new', _('Like New')),
        ('excellent', _('Excellent')),
        ('good', _('Good')),
        ('fair', _('Fair')),
        ('poor', _('Poor')),
        ('needs_work', _('Needs Work')),
        ('under_renovation', _('Under Renovation')),
        ('under_construction', _('Under Construction')),
        ('vacant', _('Vacant')),
        ('occupied', _('Occupied')),
        ('foreclosure', _('Foreclosure')),
        ('short_sale', _('Short Sale')),
        ('bank_owned', _('Bank Owned')),
        ('other', _('Other')),
    ]

    list_type = models.CharField(max_length=10, choices=LISTING_TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    has_c_of_o = models.BooleanField(default=False)
    has_deed_of_assignment = models.BooleanField(default=False)
    has_power_of_attorney = models.BooleanField(default=False)
    has_survey_plan = models.BooleanField(default=False)
    has_governors_consent = models.BooleanField(default=False)
    total_half_bathrooms = models.IntegerField(null=True, blank=True)
    total_full_bathrooms = models.IntegerField(null=True, blank=True)
    laundry_level = models.CharField(max_length=50, blank=True, null=True, choices=LEVEL_CHOICES)
    has_basement = models.BooleanField(null=True, blank=True)
    has_fireplace = models.BooleanField(null=True, blank=True)
    total_structure_area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_interior_livable_area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    finished_area_above_ground = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    finished_area_below_ground = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_parking_spaces = models.IntegerField(blank=True, null=True)
    parking_feature = models.CharField(max_length=50, blank=True, null=True, choices=PARKING_FEATURE_CHOICES)
    garage_spaces = models.IntegerField(blank=True, null=True)
    parcel_number = models.CharField(max_length=50, blank=True, null=True)
    home_type = models.CharField(max_length=50, blank=True, null=True)
    architectural_style = models.CharField(max_length=50, blank=True, null=True, choices=ARCHITECTURAL_STYLE_CHOICES)
    property_condition = models.CharField(max_length=50, blank=True, null=True,  choices=PROPERTY_CONDITION_CHOICES)
    year_built = models.IntegerField(blank=True, null=True)
    has_fitness_center = models.BooleanField(null=True, blank=True)
    has_game_room = models.BooleanField(null=True, blank=True)
    has_bicycle_storage = models.BooleanField(null=True, blank=True)
    has_swimming_pool = models.BooleanField(null=True, blank=True)
    allow_small_dog = models.BooleanField(null=True, blank=True)
    allow_large_dog = models.BooleanField(null=True, blank=True)
    allow_cat = models.BooleanField(null=True, blank=True)

    class Meta:
        verbose_name = "Home Property"
        verbose_name_plural = "Home Properties"
        ordering = ["-created_at"]
    def __str__(self):
        return f"HomeProperty: {self.address[:100]}..."

    def finished_area(self):
        """
        Calculate the finished area of the property.
        """
        if self.finished_area_above_ground and self.finished_area_below_ground:
            return self.finished_area_above_ground + self.finished_area_below_ground
        return None
    def total_bathrooms(self):
        """
        Calculate the total number of bathrooms.
        """
        if self.total_half_bathrooms and self.total_full_bathrooms:
            return self.total_half_bathrooms + self.total_full_bathrooms
        return None
    def total_bedrooms(self):
        """
        Calculate the total number of bedrooms.
        """
        if hasattr(self, 'bedrooms'):
            return self.bedrooms.count()
        return 0
    
    def save(self, *args, **kwargs):
        """
        Override the save method to set the property type based on the model.
        """
        if not self.property_type:
            self.property_type = 'home'
        return super().save(*args, **kwargs)
    

# id, level, dimention_width, dimention_height, home_id
class HomePropertyBedroom(models.Model):
    """
    HomePropertyBedroom model class
    """
    level = models.CharField(max_length=50, blank=True, null=True, choices=LEVEL_CHOICES)
    dimention_width = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    dimention_length = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    home_property = models.ForeignKey(HomeProperty, related_name="bedrooms", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Home Property Bedroom"
        verbose_name_plural = "Home Property Bedrooms"
        ordering = ["-home_property__created_at"]

    def __str__(self):
        return f"HomePropertyBedroom - {self.id}: {self.home_property.address[:100]}..."
    
    def area(self):
        """
        Calculate the area of the bedroom.
        """
        if self.dimention_width and self.dimention_length:
            return self.dimention_width * self.dimention_length
        return None


# id, price, apartment_type, has_dishwasher, has_washer, has_dryer, has_oven, has_refrigerator, property_id, property_listed_by_id, property_listed_by_user_id, property_verified_id, property_verified_user_id
class ApartmentProperty(Property):
    """
    ApartmentProperty model class
    """
    APARTMENT_TYPE_CHOICES = [
        ('studio', 'Studio'),
        ('1_bedroom', '1 Bedroom'),
        ('2_bedroom', '2 Bedroom'),
        ('3_bedroom', '3 Bedroom'),
        ('4_bedroom', '4 Bedroom'),
        ('5_bedroom', '5 Bedroom'),
        ('penthouse', 'Penthouse'),
        ('loft', 'Loft'),
        ('duplex', 'Duplex'),
        ('triplex', 'Triplex'),
        ('hotel', 'Hotel'),
        ('hostel', 'Hostel'),
        ('other', 'Other'),
    ]

    price = models.DecimalField(max_digits=10, decimal_places=2)
    apartment_type = models.CharField(max_length=50, blank=True, null=True, choices=APARTMENT_TYPE_CHOICES)
    has_dishwasher = models.BooleanField(null=True, blank=True)
    has_washer = models.BooleanField(null=True, blank=True)
    has_dryer = models.BooleanField(null=True, blank=True)
    has_oven = models.BooleanField(null=True, blank=True)
    has_refrigerator = models.BooleanField(null=True, blank=True)

    class Meta:
        verbose_name = "Apartment Property"
        verbose_name_plural = "Apartment Properties"
        ordering = ["-created_at"]

    def __str__(self):
        return f"ApartmentProperty: {self.address[:100]}..."
    
    def save(self, *args, **kwargs):
        """
        Override the save method to set the property type based on the model.
        """
        if not self.property_type:
            self.property_type = 'apartment'
        return super().save(*args, **kwargs)


class BannedProperty(models.Model):
    """
    BannedProperty model class
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, related_name="banned_properties", on_delete=models.CASCADE)
    banned_by = models.ForeignKey(User, related_name="banned_properties", on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Banned Property"
        verbose_name_plural = "Banned Properties"
        ordering = ["-created_at"]

    def __str__(self):
        return f"BannedProperty: {self.property.address[:100]}..."


class VerifiedProperty(models.Model):
    """
    VerifiedProperty model class
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.OneToOneField(Property, related_name="verified", on_delete=models.CASCADE)
    verified_by = models.ForeignKey(User, related_name="verified_properties", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Verified Property"
        verbose_name_plural = "Verified Properties"
        ordering = ["-created_at"]

    def __str__(self):
        return f"VerifiedProperty: {self.property.address[:100]}..."
    

class BookmarkedProperty(models.Model):
    """
    BookmarkedProperty model class
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, related_name="bookmarked_properties", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="bookmarked_properties", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bookmarked Property"
        verbose_name_plural = "Bookmarked Properties"
        ordering = ["-created_at"]

    def __str__(self):
        return f"BookmarkedProperty: {self.property.address[:100]}..."
