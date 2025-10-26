# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NetworkDeviceViewSet, update_host_by_identifier, delete_host_by_identifier

app_name = 'network_device'

router = DefaultRouter()
router.register(r'network-devices', NetworkDeviceViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('update-device/', update_host_by_identifier, name='update-device-by-identifier'),
    path('delete-device/', delete_host_by_identifier, name='delete-device-by-identifier'),
]