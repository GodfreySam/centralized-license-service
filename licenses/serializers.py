from rest_framework import serializers
from .models import License, LicenseKey


"""
US1: Creates or retrieves a license key and associates a new product license.
Ensures Brand A licenses don't mix with Brand B keys.
"""
class ProvisionInputSerializer(serializers.Serializer):
    customer_email = serializers.EmailField()
    product_slug = serializers.SlugField()


"""
US2: Returns the current status of a license key.
Ensures Brand A licenses don't mix with Brand B keys.
"""
class LicenseResponseSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name')
    license_key = serializers.CharField(source='license_key.key')

    class Meta:
        model = License
        fields = ['license_key', 'product_name',
                  'status', 'expires_at', 'seat_limit']


"""
US3: Activates a license for a specific instance and enforces seat limits.
"""
class ActivationInputSerializer(serializers.Serializer):
    license_key = serializers.CharField()
    product_slug = serializers.SlugField()
    instance_id = serializers.CharField()


"""
US6: Lists all licenses across all brands for a specific email.
This provides the 'Single Source of Truth' view.
"""
class EcosystemLicenseSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='product.brand.name')
    product_name = serializers.CharField(source='product.name')
    license_key = serializers.CharField(source='license_key.key')

    class Meta:
        model = License
        fields = ['brand_name', 'product_name',
                  'license_key', 'status', 'expires_at']
