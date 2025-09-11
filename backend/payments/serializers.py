from rest_framework import serializers


class PropertyCheckoutRequestSerializer(serializers.Serializer):
    property_id = serializers.CharField(max_length=255)

class PropertyCheckoutResponseSerializer(serializers.Serializer):
    payment_link = serializers.URLField()