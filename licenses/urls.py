from django.urls import path

from .views import (GlobalCustomerLicenseView, LicenseActivateView,
                    LicenseProvisionView, LicenseStatusView)

urlpatterns = [
    path('licenses/provision/', LicenseProvisionView.as_view(), name='license-provision'),
    path('licenses/<str:key>/status/', LicenseStatusView.as_view(), name='license-status'),
    path('activations/', LicenseActivateView.as_view(), name='license-activate'),
    path('customers/<str:email>/licenses/', GlobalCustomerLicenseView.as_view(), name='customer-licenses'),
]
