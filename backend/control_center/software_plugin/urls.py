# File: plugins/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PluginViewSet,
    PluginRequirementViewSet,
    PluginInstallationViewSet,
    SnifferInstallationConfigViewSet
)
app_name = 'software_plugin'
router = DefaultRouter()
router.register(r'plugins', PluginViewSet, basename='plugin')
router.register(r'plugin-requirements', PluginRequirementViewSet, basename='pluginrequirement')
router.register(r'installations', PluginInstallationViewSet, basename='plugininstallation')

router.register(r'sniffer-configs', SnifferInstallationConfigViewSet, basename='snifferinstallationconfig')

urlpatterns = [
    path('', include(router.urls)),
]
