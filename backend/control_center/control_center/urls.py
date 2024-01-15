"""
URL configuration for control_center project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from ovs_install.views import InstallOvsView
from ovs_management.views import GetDevicePorts, CreateBridge, GetDeviceBridges
from general.views import AddDeviceView, DeviceDetailsView, DeviceListView, DeviceBridgesView, DevicePortsView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('add-device/', AddDeviceView.as_view(), name='add-device'),
    path('device-details/<str:lan_ip_address>/', DeviceDetailsView.as_view(), name='device-details'),
    path('install-ovs/', InstallOvsView.as_view(), name='install-ovs'),
    path('devices/', DeviceListView.as_view(), name='device-list'),
    path('device-bridges/<str:lan_ip_address>/', DeviceBridgesView.as_view(), name='device-bridges'),
    path('device-ports/<str:lan_ip_address>/', DevicePortsView.as_view(), name='device-ports'),
    path('get-device-ports/<str:lan_ip_address>/', GetDevicePorts.as_view(), name='get-device-ports'),
    path('add-bridge/', CreateBridge.as_view(), name='add-bridge'),
    path('get-bridges/<str:lan_ip_address>/', GetDeviceBridges.as_view(), name='get-bridges'),
]
