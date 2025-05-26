from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, UserManager
from django.contrib.auth.hashers import make_password, check_password
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import random
import uuid
import string
from django.conf import settings
import os


class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError("Users must have an email address")
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    User model class
    """
    id = models.UUIDField(_("ID"), primary_key=True,
                          default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(_("email address"), unique=True)
    email_verified = models.BooleanField(_("email verified"), default=False, help_text=_("Designates whether the email has been verified."))
    firebase_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def has_google_account(self):
        return self.firebase_uid != None

    def has_phone_number(self):
        try:
            return self.phone_number is not None and self.phone_number.is_verified
        except User.phone_number.RelatedObjectDoesNotExist:
            return False

    def is_stakeholder(self):
        try:
            return self.stakeholder_account is not None
        except User.stakeholder_account.RelatedObjectDoesNotExist:
            return False


class TimeStampedBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OTPRequest(TimeStampedBaseModel):
    ref = models.TextField()
    # Hashed random token for device identity
    device_identity = models.CharField(max_length=255)
    otp = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("OTP Request")
        verbose_name_plural = _("OTP Requests")
    
    def __str__(self):
        return f"{self.ref} - {self.otp}"

    # THE DEVICE IDENTITY IS TO ENSURE THAT THE DEVICE THAT REQUESTED THE OTP IS THE SAME DEVICE THAT IS VERIFYING IT.
    # THIS IS TO PREVENT OTP REUSE ATTACKS.

    def has_expired(self):
        """
        Check if the OTP request has expired based on the expiration time.
        """
        expiration_time = timezone.timedelta(
            seconds=getattr(settings, 'OTP_EXPIRATION_TIME', 600))
        return timezone.now() > self.created_at + expiration_time

    def is_device_valid(self, device_identity):
        """
        Validate the provided device identity against the stored device identity.
        """
        return check_password(device_identity, self.device_identity)

    def is_valid(self, device_identity):
        """
        Check if the OTP request can be verified:
        - The device identity token is valid.
        - The OTP request has not expired.
        """
        return self.is_device_valid(device_identity) and not self.has_expired()

    @staticmethod
    def generate_otp():
        """
        Generate a 6-digit OTP.
        """
        return f"{random.randint(100000, 999999)}"

    @staticmethod
    def generate_device_token(length=10):
        """
        Generate a hashed random string to be used as a device identity token.
        """
        characters = string.ascii_letters + string.digits
        plain_token = ''.join(random.choice(characters) for _ in range(length))
        hashed_token = make_password(plain_token)
        return hashed_token, plain_token


class PhoneNumber(TimeStampedBaseModel):
    """
    PhoneNumber model class
    """
    # id = models.UUIDField(_("ID"), primary_key=True,
    #                       default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="phone_number")
    mobile = models.CharField(max_length=15, unique=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Phone Number")
        verbose_name_plural = _("Phone Numbers")


class StakeholderAccount(TimeStampedBaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="stakeholder_account")
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - ({'Is verified' if self.is_verified else 'Not verified'})"


def upload_identity_image(instance, filename: str):
    # Use the user's ID and the original filename to create a unique path
    root, ext = os.path.splitext(filename)
    # support only 1 upload/stakeholders
    return f"identities/{instance.user.email}.{ext}"


class GovIssuedIdentity(TimeStampedBaseModel):
    IDENTITY_CHOICES = (
        ('bvn', 'BVN'),
        ('nin', 'NIN'),
        ('national_passport', 'National Passport')
    )
    type = models.CharField(
        _("Identity Type"), max_length=50, choices=IDENTITY_CHOICES)
    image = models.ImageField(
        _("Identity Shot"),
        upload_to=upload_identity_image,
        max_length=255
    )
    stakeholder = models.OneToOneField(
        StakeholderAccount, on_delete=models.CASCADE, related_name="identity")
    
    class Meta:
        verbose_name = _("Gov Issued Identity")
        verbose_name_plural = _("Gov Issued Identities")
