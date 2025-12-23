from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from .models import Brand, Product, LicenseKey, License, Activation
from .services import LicenseService


class LicenseActivationTests(TestCase):
    def setUp(self):
        # 1. Setup the Brand and Product for testing
        self.brand = Brand.objects.create(name="RankMath")
        self.product = Product.objects.create(
            brand=self.brand,
            name="RankMath SEO",
            slug="rankmath-seo",
            default_seats=1  # We'll test with a 1-seat limit
        )

        # 2. Provision a license for a customer
        self.license = LicenseService.provision_license(
            brand=self.brand,
            customer_email="godfreysam09@gmail.com",
            product_slug="rankmath-seo"
        )
        self.license_key = self.license.license_key.key

    def test_successful_activation(self):
        """Tests that a license can be activated when seats are available."""
        activation = LicenseService.activate_license(
            key_string=self.license_key,
            product_slug="rankmath-seo",
            instance_id="https://www.godfreyo.link"
        )
        self.assertEqual(activation.instance_id, "https://www.godfreyo.link")
        self.assertEqual(Activation.objects.count(), 1)

    def test_seat_limit_enforcement(self):
        """US3: Tests that activation fails when seat limit is exceeded."""
        # Activate the first (and only) seat
        LicenseService.activate_license(
            key_string=self.license_key,
            product_slug="rankmath-seo",
            instance_id="https://www.godfreyo.link"
        )

        # Attempt to activate a second seat (different instance)
        with self.assertRaises(PermissionDenied) as context:
            LicenseService.activate_license(
                key_string=self.license_key,
                product_slug="rankmath-seo",
                instance_id="https://www.godfreyo-second.link"
            )

        self.assertIn("Seat limit reached", str(context.exception))
        # Ensure the second activation record wasn't created
        self.assertEqual(Activation.objects.count(), 1)

    def test_idempotent_activation(self):
        """Tests that activating the same site twice doesn't consume extra seats."""
        # Activate site once
        LicenseService.activate_license(
            key_string=self.license_key,
            product_slug="rankmath-seo",
            instance_id="https://www.godfreyo.link"
        )

        # Activate site again (idempotency check)
        LicenseService.activate_license(
            key_string=self.license_key,
            product_slug="rankmath-seo",
            instance_id="https://www.godfreyo.link"
        )

        self.assertEqual(Activation.objects.count(), 1)
