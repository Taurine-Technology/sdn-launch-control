from django.urls import re_path
from device_monitoring.consumers import DeviceConsumer

websocket_urlpatterns = [
    re_path(r'^ws/device_stats/$', DeviceConsumer.as_asgi()),
]
