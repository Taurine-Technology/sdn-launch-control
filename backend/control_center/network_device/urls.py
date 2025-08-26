# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NetworkDeviceViewSet
app_name = 'network_device'
router = DefaultRouter()
router.register(r'network-devices', NetworkDeviceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
