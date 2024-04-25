from django.urls import re_path
from device_monitoring.consumers import DeviceConsumer, OpenFlowMetricsConsumer

websocket_urlpatterns = [
    re_path(r'^ws/device_stats/$', DeviceConsumer.as_asgi()),
    re_path(r'^ws/openflow_metrics/$', OpenFlowMetricsConsumer.as_asgi()),
]
