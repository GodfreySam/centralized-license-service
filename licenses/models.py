import uuid

from django.db import models


class Brand(models.Model):
    """Represents a tenant in the system (e.g., RankMath, WP Rocket)."""
    name = models.CharField(max_length=255, unique=True)
    api_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    """A specific software product owned by a Brand."""
    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    slug = models.SlugField()  # e.g., 'content-ai'
    default_seats = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('brand', 'slug')

    def __str__(self):
        return f"{self.brand.name} - {self.name}"


class LicenseKey(models.Model):
    """The 'container' for licenses. A user gets one key per brand."""
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    key = models.CharField(max_length=255, unique=True,
                           default=uuid.uuid4)
    customer_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensures a customer has one key per brand for simplicity
        unique_together = ('brand', 'customer_email')

    def __str__(self):
        return f"{self.key} ({self.customer_email})"


class License(models.Model):
    """The specific entitlement for a product."""
    STATUS_CHOICES = [
        ('valid', 'Valid'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
    ]

    license_key = models.ForeignKey(
        LicenseKey, on_delete=models.CASCADE, related_name='licenses')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='valid')
    expires_at = models.DateTimeField(null=True, blank=True)
    seat_limit = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} - {self.status}"


class Activation(models.Model):
    """Tracks specific instances where a license is active (seats)."""
    license = models.ForeignKey(
        License, on_delete=models.CASCADE, related_name='activations')
    # e.g., site URL or Machine ID
    instance_id = models.CharField(max_length=255)
    activated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('license', 'instance_id')
