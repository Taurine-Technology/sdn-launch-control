from django.urls import re_path
from device_monitoring.consumers import DeviceConsumer, OpenFlowMetricsConsumer
from classifier.consumers import FlowConsumer
websocket_urlpatterns = [
    re_path(r'^ws/device_stats/$', DeviceConsumer.as_asgi()),
    re_path(r'^ws/openflow_metrics/$', OpenFlowMetricsConsumer.as_asgi()),
    re_path(r'^ws/flow_updates/$', FlowConsumer.as_asgi()),
]
