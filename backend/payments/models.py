from django.db import models
from properties.models import Property
from django.contrib.auth import get_user_model
from django.utils import timezone
from utilities import idx


class Payment(models.Model):
    id = models.CharField(
        primary_key=True,
        editable=False,
        default=idx.generate_payment_id,
        max_length=255,
        help_text="Payment ID from the payment gateway (e.g., Flutterwave).",
    )
    unit_amount = models.IntegerField(
        help_text="Amount in the smallest currency unit"
    )
    currency = models.CharField(max_length=10, default='NGN')

    def amount(self):
        return self.unit_amount / 100.0

    def __str__(self):
        return f"{self.checkout.payment_gateway.title()} - {self.currency}{self.amount()}"


class Checkout(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    PAYMENT_GATEWAY_CHOICES = [
        ('flutterwave', 'Flutterwave'),
    ]
    
    id = models.CharField(
        primary_key=True, 
        editable=False, 
        max_length=255,
        default=idx.generate_checkout_id,
        help_text="A weak identifier for the checkout session. Default is a {idx.generate_checkout_id}."
    )
    payment = models.OneToOneField(Payment, on_delete=models.PROTECT, related_name='checkout', null=True, blank=True)
    payment_gateway = models.CharField(max_length=100, choices=PAYMENT_GATEWAY_CHOICES)
    status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='initiated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)


class PropertyCheckout(Checkout):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Property Checkout"
        verbose_name_plural = "Property Checkouts"
        ordering = ["-created_at"]