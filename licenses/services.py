from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Activation, License, LicenseKey, Product


class LicenseService:
    @staticmethod
    @transaction.atomic
    def provision_license(brand, customer_email, product_slug):
        """
        US1: Creates or retrieves a license key and associates a new product license.
        Ensures Brand A licenses don't mix with Brand B keys.
        """
        # 1. Get or create the unique key for this brand + email
        license_key, created = LicenseKey.objects.get_or_create(
            brand=brand,
            customer_email=customer_email
        )

        # 2. Get the product (scoped to the brand)
        try:
            product = Product.objects.get(brand=brand, slug=product_slug)
        except Product.DoesNotExist:
            raise ValidationError(
                f'Product "{product_slug}" not found for brand "{brand.name}"'
            )

        # 3. Create the specific license (entitlement)
        # Default expiration to 1 year for this example
        license = License.objects.create(
            license_key=license_key,
            product=product,
            status='valid',
            expires_at=timezone.now() + timedelta(days=365),
            seat_limit=product.default_seats
        )

        return license

    @staticmethod
    @transaction.atomic
    def activate_license(key_string, product_slug, instance_id):
        """
        US3: Activates a license for a specific instance and enforces seat limits.
        """
        # 1. Fetch the license key and the specific product license
        try:
            license_obj = License.objects.select_related('license_key').get(
                license_key__key=key_string,
                product__slug=product_slug
            )
        except License.DoesNotExist:
            raise ValidationError(
                f'License not found for key "{key_string}" and product "{product_slug}"'
            )

        # 2. Check lifecycle status (US2/US4 logic)
        if license_obj.status != 'valid':
            raise PermissionDenied(
                f"License is currently {license_obj.status}.")

        if license_obj.expires_at and license_obj.expires_at < timezone.now():
            raise PermissionDenied("License has expired.")

        # 3. Handle Idempotency (Is this instance already activated?)
        activation, created = Activation.objects.get_or_create(
            license=license_obj,
            instance_id=instance_id
        )

        if created:
            # 4. Enforce seat limits
            current_seats = Activation.objects.filter(
                license=license_obj).count()
            if current_seats > license_obj.seat_limit:
                # Rollback the creation if limit is exceeded
                activation.delete()
                raise PermissionDenied(
                    "Seat limit reached. Deactivate another site first.")

        return activation

    @staticmethod
    @transaction.atomic
    def list_customer_licenses(email):
        """
        US6: Lists all licenses across all brands for a specific email.
        This provides the 'Single Source of Truth' view.
        """
        return License.objects.filter(
            license_key__customer_email=email
        ).select_related('product', 'product__brand', 'license_key')
