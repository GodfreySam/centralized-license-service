from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Activation, Brand, License
from .serializers import (ActivationInputSerializer,
                          EcosystemLicenseSerializer,
                          LicenseResponseSerializer, ProvisionInputSerializer)
from .services import LicenseService


@extend_schema(
    summary='Provision a license',
    description='Creates or retrieves a license key and associates a new product license. If the customer already has a key for this brand, it reuses it.',
    request=ProvisionInputSerializer,
    responses={201: LicenseResponseSerializer, 400: None, 404: None},
    tags=['Licenses'],
)
class LicenseProvisionView(APIView):
    def post(self, request):
        serializer = ProvisionInputSerializer(data=request.data)
        if serializer.is_valid():
            # In a real app, 'brand' would come from an API Key in the headers
            # For the demo, we'll assume the brand name is passed or hardcoded
            brand_name = request.headers.get('X-Brand-Name', 'RankMath')
            try:
                brand = Brand.objects.get(name=brand_name)
            except Brand.DoesNotExist:
                return Response(
                    {'error': f'Brand "{brand_name}" not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            try:
                license = LicenseService.provision_license(
                    brand=brand,
                    customer_email=serializer.validated_data['customer_email'],
                    product_slug=serializer.validated_data['product_slug']
                )
            except Exception as e:
                # Handle service layer errors (Product.DoesNotExist, etc.)
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

            output = LicenseResponseSerializer(license)
            return Response(output.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary='Activate a license seat',
    description='Activates a license for a specific instance (e.g., site URL). Validates the license, checks expiration, and enforces seat limits. Idempotent - safe to call multiple times.',
    request=ActivationInputSerializer,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'activated'},
                'instance_id': {'type': 'string', 'example': 'https://my-site.com'},
                'activated_at': {'type': 'string', 'format': 'date-time'},
            }
        },
        400: None,
        403: None,
    },
    tags=['Activations'],
)
class LicenseActivateView(APIView):
    """
    Endpoint for end-user products to activate usage.
    """

    def post(self, request):
        serializer = ActivationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        activation = LicenseService.activate_license(
            key_string=serializer.validated_data['license_key'],
            product_slug=serializer.validated_data['product_slug'],
            instance_id=serializer.validated_data['instance_id']
        )

        return Response({
            "status": "activated",
            "instance_id": activation.instance_id,
            "activated_at": activation.activated_at
        }, status=status.HTTP_200_OK)


@extend_schema(
    summary='Get license status',
    description='Returns the current status of a license key including validity, expiration, seat limits, and remaining seats.',
    parameters=[
        OpenApiParameter(
            name='key',
            type=str,
            location=OpenApiParameter.PATH,
            description='The license key to check',
            required=True,
        ),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'license_key': {'type': 'string'},
                'product_name': {'type': 'string'},
                'status': {'type': 'string', 'enum': ['valid', 'suspended', 'cancelled']},
                'is_valid': {'type': 'boolean'},
                'expires_at': {'type': 'string', 'format': 'date-time', 'nullable': True},
                'seat_limit': {'type': 'integer'},
                'active_seats': {'type': 'integer'},
                'remaining_seats': {'type': 'integer'},
            }
        },
        404: None,
    },
    tags=['Licenses'],
)
class LicenseStatusView(APIView):
    """
    US4: Returns the current status of a license key.
    """

    def get(self, request, key):
        try:
            license_obj = License.objects.select_related('license_key', 'product').get(
                license_key__key=key
            )

            # Count active activations
            active_seats = Activation.objects.filter(
                license=license_obj).count()
            remaining_seats = max(0, license_obj.seat_limit - active_seats)

            # Check if expired
            is_expired = license_obj.expires_at and license_obj.expires_at < timezone.now()
            is_valid = license_obj.status == 'valid' and not is_expired

            return Response({
                'license_key': key,
                'product_name': license_obj.product.name,
                'status': license_obj.status,
                'is_valid': is_valid,
                'expires_at': license_obj.expires_at,
                'seat_limit': license_obj.seat_limit,
                'active_seats': active_seats,
                'remaining_seats': remaining_seats,
            })
        except License.DoesNotExist:
            return Response(
                {'error': 'License not found'},
                status=status.HTTP_404_NOT_FOUND
            )


@extend_schema(
    summary='List all licenses for a customer',
    description='Returns all licenses associated with a customer email across all brands. This is an admin-only endpoint that bypasses brand isolation.',
    parameters=[
        OpenApiParameter(
            name='email',
            type=str,
            location=OpenApiParameter.PATH,
            description='Customer email address',
            required=True,
        ),
    ],
    responses={200: EcosystemLicenseSerializer(many=True)},
    tags=['Admin'],
)
class GlobalCustomerLicenseView(APIView):
    """
    US6: Ecosystem-wide view for internal systems/brands.
    In a real scenario, use: permission_classes = [IsAuthenticated, IsInternalSystem]
    """

    def get(self, request, email):
        licenses = LicenseService.list_customer_licenses(email)
        serializer = EcosystemLicenseSerializer(licenses, many=True)
        return Response(serializer.data)
