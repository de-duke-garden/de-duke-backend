from django.db import models
import uuid
from django.contrib.gis.db.models import PointField
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from accounts.models import HostAccount
import googlemaps
from django.conf import settings
import logging

from utilities.helpers import property_image_upload_handler, property_media_upload_handler
from utilities import idx


logger = logging.getLogger("django")


User = get_user_model()

LEVEL_CHOICES = [
    ("ground", "Ground"),
    ("basement", "Basement"),
    ("first", "First"),
    ("second", "Second"),
    ("third", "Third"),
]

class Property(models.Model):
    """
    Property model class
    """
    PROPERTY_TYPE_CHOICES = [
        ('shortlet', 'Shortlet'),
        ('commercial', 'Commercial'),
    ]
    id = models.CharField(
        primary_key=True,
        max_length=255,
        default=idx.generate_property_id,
        editable=False
    )
    address = models.TextField(null=False, blank=True, help_text="Address of the property (leave blank for reverse geocoding)")
    location = PointField(geography=True, null=False, blank=False)
    description = models.TextField()    
    # special_tags = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    last_checked = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    listed_by = models.ForeignKey(HostAccount, related_name="properties", on_delete=models.CASCADE)
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPE_CHOICES)

    class Meta:
        verbose_name = "Property"
        verbose_name_plural = "Properties"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Property at {self.address[:100]}... by {self.listed_by.user.email if self.listed_by and self.listed_by.user else 'Unknown'}"
    
    def is_banned(self):
        """
        Check if the property is banned.
        """
        return hasattr(self, 'banned') and self.banned is not None
    
    def is_verified(self):
        """
        Check if the property is verified.
        """
        # return hasattr(self, 'verified') and self.verified is not None
        return hasattr(self, 'verified') and self.verified.is_verified()
    
    def is_verified_by(self):
        """
        Check if the property is verified by a user.
        """
        if hasattr(self, 'verified'):
            return self.verified.verified_by
        return None
    
    @property
    def price(self):
        """
        Get the price of the property based on its type.
        """
        if self.property_type == "commercial":
            commercial = getattr(self, 'commercialproperty', None)
            if commercial:
                return commercial.price
        elif self.property_type == "shortlet":
            shortlet = getattr(self, 'shortletproperty', None)
            if shortlet:
                return shortlet.price
        return None
    
    def title(self):
        """
        Generate a title for the property based on its type and key attributes.
        """
        return self.address if self.address else "Property"
    
    def subtitle(self):
        """
        Generate a subtitle for the property based on its type and key attributes.
        """
        if self.property_type == "commercial":
            commercial = getattr(self, 'commercialproperty', None)
            if commercial:
                return commercial.subtitle()
        elif self.property_type == "shortlet":
            shortlet = getattr(self, 'shortletproperty', None)
            if shortlet:
                return shortlet.subtitle()
        return "Property"
    
    def tag(self):
        """
        Generate a tag for the property based on its type.
        """
        if self.property_type == "commercial":
            commercial = getattr(self, 'commercialproperty', None)
            if commercial:
                return commercial.tag()
        elif self.property_type == "shortlet":
            shortlet = getattr(self, 'shortletproperty', None)
            if shortlet:
                return shortlet.tag()
        return "Property"
    
    def features(self):
        """
        Generate a features string for the property based on its type and key attributes.
        """
        if self.property_type == "commercial":
            commercial = getattr(self, 'commercialproperty', None)
            if commercial:
                return commercial.features()
        elif self.property_type == "shortlet":
            shortlet = getattr(self, 'shortletproperty', None)
            if shortlet:
                return shortlet.features()
        return ""
    
    def amenities(self):
        """
        Generate an amenities string for the property based on its type and key attributes.
        """
        if self.property_type == "commercial":
            commercial = getattr(self, 'commercialproperty', None)
            if commercial:
                return commercial.amenities()
        elif self.property_type == "shortlet":
            shortlet = getattr(self, 'shortletproperty', None)
            if shortlet:
                return shortlet.amenities()
        return ""
    
    def primary_image(self):
        """
        Get the primary image of the property.
        """
        primary_image = self.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image
        first_image = self.images.first()
        if first_image:
            return first_image.image
        return None


class PropertyImage(models.Model):
    """
    PropertyImage model class
    """
    id = models.CharField(
        primary_key=True,
        max_length=255,
        default=idx.generate_property_image_id,
        editable=False
    )
    image = models.ImageField(upload_to=property_image_upload_handler)
    property = models.ForeignKey(Property, related_name="images", on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Property Image"
        verbose_name_plural = "Property Images"
        ordering = ["-property__created_at"]

    def __str__(self):
        return self.property.__str__()
    

# class PropertyMedia(models.Model):
#     """
#     PropertyMedia model class
#     """
#     id = models.CharField(
#         primary_key=True,
#         max_length=255,
#         default=idx.generate_property_media_id,
#         editable=False
#     )
#     image = models.FileField(upload_to=property_media_upload_handler)
#     property = models.ForeignKey(Property, related_name="media", on_delete=models.CASCADE)
#     is_primary = models.BooleanField(default=False)

#     class Meta:
#         verbose_name = "Property Media"
#         verbose_name_plural = "Property Media"
#         ordering = ["-property__created_at"]

#     def __str__(self):
#         return self.property.__str__()


class CommercialProperty(Property):
    """
    CommercialProperty model class
    """
    LISTING_TYPE_CHOICES = [
        ('Sale', 'Sale'),
        ('Lease', 'Lease'),
    ]
    
    COMMERCIAL_TYPE_CHOICES = [
        ('Office', _('Office')),
        ('Shop', _('Shop')),
        ('Home', _('Home')),
        ('land', _('Land')),
    ]

    PARKING_FEATURE_CHOICES = [
        ('Attached', 'Attached'),
        ('Detached', 'Detached'),
        ('Carport', 'Carport'),
        ('Street', 'Street'),
    ]

    ARCHITECTURAL_STYLE_CHOICES = [
        ('Modern', _('Modern')),
        ('Traditional', _('Traditional')),
        ('Industrial', _('Industrial')),
    ]

    PROPERTY_CONDITION_CHOICES = [
        ('New', _('New')),
        ('Under Renovation', _('Under Renovation')),
        ('Under Construction', _('Under Construction')),
        ('Bank Owned', _('Bank Owned')),
    ]

    listing_type = models.CharField(max_length=10, choices=LISTING_TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    possession_period_days = models.IntegerField(null=True, blank=True, help_text="Number of days a lessee can take possession after signing the lease")
    is_sold = models.BooleanField(default=False)
    has_c_of_o = models.BooleanField(default=False)
    has_deed_of_assignment = models.BooleanField(default=False)
    has_power_of_attorney = models.BooleanField(default=False)
    has_survey_plan = models.BooleanField(default=False)
    has_governors_consent = models.BooleanField(default=False)
    total_bathrooms = models.IntegerField(null=True, blank=True)
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
    commercial_type = models.CharField(max_length=50, choices=COMMERCIAL_TYPE_CHOICES)
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
        verbose_name = "Commercial Property"
        verbose_name_plural = "Commercial Properties"
        ordering = ["-created_at"]

    def finished_area(self):
        """
        Calculate the finished area of the property.
        """
        # if self.finished_area_above_ground and self.finished_area_below_ground:
        #     return self.finished_area_above_ground + self.finished_area_below_ground
        # return None
        return (self.finished_area_above_ground or 0) + (self.finished_area_below_ground or 0)
    
    def total_rooms(self):
        """
        Calculate the total number of rooms in the property.
        """
        if hasattr(self, 'rooms'):
            return self.rooms.count()
        return 0

    def is_bookmarked(self, user):
        """
        Check if the property is bookmarked by the given user.
        """
        return self.bookmarked_properties.filter(user=user).exists()
    
    def subtitle(self):
        subtitle = ""
        # if self.commercial_type:
        #     subtitle += f"{self.commercial_type} | "
        # if self.architectural_style:
        #     subtitle += f"{self.architectural_style} | "
        # if self.property_condition:
        #     subtitle += f"{self.property_condition} | "
        # if self.total_bathrooms:
        #     subtitle += f"{self.total_bathrooms} Bath | "
        # if self.total_rooms():
        #     subtitle += f"{self.total_rooms()} Rooms | "
        # if self.listing_type == "Sale":
        #     subtitle += f"For Sale"
        # elif self.listing_type == "Lease":
        #     subtitle += f"{self.possession_period_days} days possession period"
        if self.listing_type == "Sale":
            subtitle = f"{self.commercial_type} Available for Sale"
        elif self.listing_type == "Lease":
            subtitle = f"{self.commercial_type} Available for {self.possession_period_days}-Days Lease"
        return subtitle

    def tag(self):
        return self.commercial_type if self.commercial_type else "Commercial"
    
    def features(self):
        features = []
        features.append(self.listing_type)
        if self.listing_type == "Lease" and self.possession_period_days:
            features.append(f"{self.possession_period_days} Days")
        if self.total_bathrooms:
            features.append(f"{self.total_bathrooms} Bath")
        if self.total_rooms():
            features.append(f"{self.total_rooms()} Rooms")
        if self.architectural_style:
            features.append(self.architectural_style)
        if self.property_condition:
            features.append(self.property_condition)
        if self.total_structure_area:
            features.append(f"{self.total_structure_area} sqft Structure Area")
        if self.total_interior_livable_area:
            features.append(f"{self.total_interior_livable_area} sqft Livable Area")
        if self.finished_area_above_ground:
            features.append(f"{self.finished_area_above_ground} sqft Above Ground")
        if self.finished_area_below_ground:
            features.append(f"{self.finished_area_below_ground} sqft Below Ground")
        if self.finished_area():
            features.append(f"{self.finished_area()} sqft Finished Area")
        if self.total_parking_spaces:
            features.append(f"{self.total_parking_spaces} Parking Spaces")
        if self.parking_feature:
            features.append(f"{self.parking_feature} Parking")
        if self.garage_spaces:
            features.append(f"{self.garage_spaces} Garage Spaces")
        if self.year_built:
            features.append(f"Built in {self.year_built}")
        
        return " | ".join(features)
    
    def amenities(self):
        amenities = []
        if self.has_basement:
            amenities.append("Basement")
        if self.has_fireplace:
            amenities.append("Fireplace")
        if self.has_fitness_center:
            amenities.append("Fitness Center")
        if self.has_game_room:
            amenities.append("Game Room")
        if self.has_bicycle_storage:
            amenities.append("Bicycle Storage")
        if self.has_swimming_pool:
            amenities.append("Swimming Pool")
        if self.allow_small_dog:
            amenities.append("Small Dog Allowed")
        if self.allow_large_dog:
            amenities.append("Large Dog Allowed")
        if self.allow_cat:
            amenities.append("Cat Allowed")
        
        return " | ".join(amenities)
    
    def save(self, *args, **kwargs):
        """
        Override the save method to set the property type based on the model.
        """
        if not self.property_type:
            self.property_type = 'commercial'
        if not self.possession_period_days and self.listing_type == 'Lease':
            # Default possession period for lease is 365 days = 1 year
            self.possession_period_days = 365
        if self.listing_type == 'Sale':
            self.possession_period_days = None
        return super().save(*args, **kwargs)
    

class CommercialPropertyRoom(models.Model):
    """
    CommercialPropertyRoom model class
    """
    id = models.CharField(
        primary_key=True,
        max_length=255,
        default=idx.generate_property_room_id,
        editable=False
    )
    level = models.CharField(max_length=50, choices=LEVEL_CHOICES)
    dimention_width = models.DecimalField(max_digits=10, decimal_places=2)
    dimention_length = models.DecimalField(max_digits=10, decimal_places=2)
    property = models.ForeignKey(CommercialProperty, related_name="rooms", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Home Property Room"
        verbose_name_plural = "Home Property Rooms"
        ordering = ["-property__created_at"]

    def __str__(self):
        return self.property.__str__()
    
    def area(self):
        """
        Calculate the area of the bedroom.
        """
        if self.dimention_width and self.dimention_length:
            return self.dimention_width * self.dimention_length
        return None


class ShortletProperty(Property):
    """
    ShortletProperty model class
    """
    SHORTLET_TYPE_CHOICES = [
        ('Hostel', 'Hostel'),
        ('Hotel', 'Hotel'),
        ('1 Bedroom', '1 Bedroom'),
        ('2 Bedroom', '2 Bedroom'),
        ('3 Bedroom', '3 Bedroom'),
    ]

    price = models.DecimalField(max_digits=10, decimal_places=2)
    possession_period_days = models.IntegerField(help_text="Number of days a tenant can take possession after signing the shortlet agreement")
    shortlet_type = models.CharField(max_length=50, choices=SHORTLET_TYPE_CHOICES)
    total_bathrooms = models.IntegerField(null=True, blank=True)
    has_dishwasher = models.BooleanField(null=True, blank=True)
    has_washer = models.BooleanField(null=True, blank=True)
    has_dryer = models.BooleanField(null=True, blank=True)
    has_oven = models.BooleanField(null=True, blank=True)
    has_refrigerator = models.BooleanField(null=True, blank=True)

    class Meta:
        verbose_name = "Shortlet Property"
        verbose_name_plural = "Shortlet Properties"
        ordering = ["-created_at"]
    
    def is_bookmarked(self, user):
        """
        Check if the property is bookmarked by the given user.
        """
        return self.bookmarked_properties.filter(user=user).exists()

    def subtitle(self):
        subtitle = ""
        # if self.shortlet_type:
        #     subtitle += f"{self.shortlet_type} | "
        # if self.has_dishwasher:
        #     subtitle += f"Dishwasher | "
        # if self.has_washer:
        #     subtitle += f"Washer | "
        # if self.has_dryer:
        #     subtitle += f"Dryer | "
        # if self.has_oven:
        #     subtitle += f"Oven | "
        # if self.has_refrigerator:
        #     subtitle += f"Refrigerator | "
        # subtitle += f"{self.possession_period_days} days possession period"
        subtitle = f"{self.shortlet_type} Available for {self.possession_period_days}-Days Rent"
        return subtitle
    
    def tag(self):
        return self.shortlet_type if self.shortlet_type else "Shortlet"
    
    def features(self):
        features = []
        features.append("Rent")
        features.append(f"{self.possession_period_days} Days")
        if self.total_bathrooms:
            features.append(f"{self.total_bathrooms} Bath")
        
        return " | ".join(features)
    
    def amenities(self):
        amenities = []
        if self.has_dishwasher:
            amenities.append("Dishwasher")
        if self.has_washer:
            amenities.append("Washer")
        if self.has_dryer:
            amenities.append("Dryer")
        if self.has_oven:
            amenities.append("Oven")
        if self.has_refrigerator:
            amenities.append("Refrigerator")
        
        return " | ".join(amenities)
    
    def save(self, *args, **kwargs):
        """
        Override the save method to set the property type based on the model.
        """
        if not self.property_type:
            self.property_type = 'shortlet'
        return super().save(*args, **kwargs)


class BannedProperty(models.Model):
    """
    BannedProperty model class
    """
    id = models.CharField(
        primary_key=True,
        max_length=255,
        default=idx.generate_banned_property_id,
        editable=False
    )
    property = models.OneToOneField(Property, related_name="banned", on_delete=models.CASCADE)
    banned_by = models.ForeignKey(User, related_name="banned_properties", on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Banned Property"
        verbose_name_plural = "Banned Properties"
        ordering = ["-created_at"]

    def __str__(self):
        return self.property.__str__()


class VerifiedProperty(models.Model):
    """
    VerifiedProperty model class
    """
    VERIFICATION_PHASE_CHOICES = [
        ('Pending', 'Pending'),
        ('Phase 1', 'Phase 1'),
        ('Phase 2', 'Phase 2'),
        ('Verified', 'Verified'),
        ('Rejected', 'Rejected'),
    ]
    id = models.CharField(
        primary_key=True,
        max_length=255,
        default=idx.generate_verified_property_id,
        editable=False
    )
    property = models.OneToOneField(Property, related_name="verified", on_delete=models.CASCADE)
    verified_by = models.ForeignKey(User, related_name="verified_properties", on_delete=models.CASCADE)
    verification_phase = models.CharField(max_length=50, choices=VERIFICATION_PHASE_CHOICES, default='Pending')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Verified Property"
        verbose_name_plural = "Verified Properties"
        ordering = ["-created_at"]

    def __str__(self):
        return self.property.__str__()
    
    def is_verified(self):
        """
        Check if the property is fully verified.
        """
        return self.verification_phase == 'Verified'
    

class BookmarkedProperty(models.Model):
    """
    BookmarkedProperty model class
    """
    id = models.CharField(
        primary_key=True,
        max_length=255,
        default=idx.generate_bookmarked_property_id,
        editable=False
    )
    property = models.ForeignKey(Property, related_name="bookmarked_properties", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="bookmarked_properties", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bookmarked Property"
        verbose_name_plural = "Bookmarked Properties"
        ordering = ["-created_at"]

    def __str__(self):
        return self.property.__str__()


class InterestedProperty(models.Model):
    """
    InterestedProperty model class
    """
    id = models.CharField(
        primary_key=True,
        max_length=255,
        default=idx.generate_interested_property_id,
        editable=False
    )
    property = models.ForeignKey(Property, related_name="interested_properties", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="interested_properties", on_delete=models.CASCADE)
    responder = models.ForeignKey(User, related_name="responded_interested_properties", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Interested Property"
        verbose_name_plural = "Interested Properties"
        ordering = ["-updated_at"]

    def __str__(self):
        return self.property.__str__()
    
    def owner(self):
        """
        Get the owner of the property.
        """
        return self.property.listed_by.user if self.property and self.property.listed_by else None


class InterestedPropertyDialog(models.Model):
    """
    InterestedPropertyDialog model class
    """
    id = models.CharField(
        primary_key=True,
        max_length=255,
        default=idx.generate_interested_property_dialogue_id,
        editable=False
    )
    interested_property = models.ForeignKey(InterestedProperty, related_name="dialogs", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name="sent_interested_property_dialogs", on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Interested Property Dialog"
        verbose_name_plural = "Interested Property Dialogs"
        ordering = ["created_at"]