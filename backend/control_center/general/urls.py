from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ControllerViewSet, SwitchViewSet, PortViewSet

app_name = 'general'

# Create a router and register the ViewSets
router = DefaultRouter()
router.register(r'controllers', ControllerViewSet, basename='controller')
router.register(r'switches', SwitchViewSet, basename='switch')
router.register(r'ports', PortViewSet, basename='port')

urlpatterns = [
    path('', include(router.urls)),
]
