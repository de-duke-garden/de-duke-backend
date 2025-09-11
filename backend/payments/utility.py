from properties.models import Property
from utilities import idx
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import requests

from .models import PropertyCheckout


User = get_user_model()


def create_property_flutterwave_payment_link(property_instance: Property, user: AbstractUser) -> str:
    """
    Create a Flutterwave payment link for a property checkout session.
    """
    url = "https://api.flutterwave.com/v3/payments"
    checkout = PropertyCheckout.objects.create(
        property=property_instance,
        user=user,
        payment_gateway='flutterwave',
        status='initiated'
    )
    payload = {
        "amount": str(int(property_instance.price)),
        "tx_ref": str(checkout.id),
        "currency": "NGN",
        "redirect_url": settings.FLUTTERWAVE_REDIRECT_URL,
        "customer": {
            "email": user.email,
            "name": f"{user.get_full_name()}"
        },
        "customizations": {
            "title": "Duke Real Estate",
            "description": f"Payment for {property_instance.subtitle()}",
            "logo": "https://de-duke.com/static/logo.png"
        },
        "configuration": { "session_duration": 30 },
        "max_retry_attempt": 5,
        "payment_options": "card, opay, banktransfer, account, applepay, googlepay, enaira",
        # "link_expiration": "2024-02-14T12:20:00",
        "meta": {
            "property_id": str(property_instance.id),
            "user_id": str(user.id),
            # "valid_until": checkout.created_at.isoformat()
        }
    }
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + settings.FLUTTERWAVE_SECRET_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        if response_data.get("status") == "success":
            payment_link = response_data["data"]["link"]
            return payment_link
        else:
            raise Exception(f"Flutterwave API error: {response_data.get('message')}")
    else:
        raise Exception(f"HTTP error: {response.status_code} - {response.text}")