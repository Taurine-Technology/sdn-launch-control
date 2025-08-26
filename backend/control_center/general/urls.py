from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ControllerViewSet, SwitchViewSet

app_name = 'general'

# Create a router and register the ControllerViewSet
router = DefaultRouter()
router.register(r'controllers', ControllerViewSet, basename='controller')
router.register(r'switches', SwitchViewSet, basename='switch')

urlpatterns = [
    path('', include(router.urls)),
]
