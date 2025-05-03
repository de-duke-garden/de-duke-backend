from rest_framework import serializers
from .models import User, PhoneNumber, GoogleAccount, StakeholderAccount, GovIssuedIdentity


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    has_google_account = serializers.BooleanField(read_only=True)
    has_phone_number = serializers.BooleanField(read_only=True)
    phone_number = serializers.CharField(
        source='get_phone_number', read_only=True, allow_null=True)
    is_stakeholder = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'is_active', 'date_joined',
                  'last_login', 'has_google_account', 'has_phone_number', 'phone_number', 'is_stakeholder']
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_active']

    def get_phone_number(self, obj):
        """
        Returns the phone number of the user if it exists and is verified.
        """
        if obj.has_phone_number():
            return obj.phone_number.mobile
        return None


class PhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        fields = ['mobile', 'is_verified']
        read_only_fields = ['is_verified']


class UserMeSerializer(serializers.ModelSerializer):
    phone_number = PhoneNumberSerializer(required=False, read_only=True)
    class Meta:
        model = User
        exclude = ['password', 'is_superuser', 'is_staff']
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_active', 'is_staff',
                            'is_superuser', 'email_verified', 'email', 'groups', 'user_permissions']


class ChangeAccountPasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()


class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    device_identity = serializers.CharField(max_length=255)


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(min_length=6)
    device_identity = serializers.CharField(max_length=255)


class ResetPasswordWithTokenSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=6)


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    device_identity = serializers.CharField(max_length=255)


class VerifyEmailWithTokenSerializer(serializers.Serializer):
    token = serializers.CharField()
