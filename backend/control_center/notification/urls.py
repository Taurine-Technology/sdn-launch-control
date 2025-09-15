# notification/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, TelegramTestView, LinkTelegramView, NetworkSummaryNotificationViewSet, DataUsageNotificationViewSet, ApplicationUsageNotificationViewSet
from .ui_views import NetworkNotificationViewSet

app_name = 'notification'

router = DefaultRouter()
router.register(r"app-usage-alerts", ApplicationUsageNotificationViewSet, basename="app-usage-alerts")
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r"network-summary", NetworkSummaryNotificationViewSet, basename="network-summary")
router.register(r"data-usage-alerts", DataUsageNotificationViewSet, basename="data-usage-alerts")
router.register(r"network-notifications", NetworkNotificationViewSet, basename="network-notifications")

urlpatterns = [
    path('notifications/test-telegram/', TelegramTestView.as_view(), name='test-telegram'),
    path('notifications/link-telegram/', LinkTelegramView.as_view(), name='link-telegram'),
    path('', include(router.urls)),
]
