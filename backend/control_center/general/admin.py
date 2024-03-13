from django.contrib import admin

# Register your models here.
from .models import Device, Bridge, Port, Controller


@admin.register(Device)
class NetworkDeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'lan_ip_address', 'device_type', 'os_type', 'ovs_enabled')


@admin.register(Bridge)
class DeviceBridgeAdmin(admin.ModelAdmin):
    list_display = ('device', 'name', 'dpid')


@admin.register(Port)
class BridgePorts(admin.ModelAdmin):
    list_display = ('name', 'device')


@admin.register(Controller)
class ControllerAdmin(admin.ModelAdmin):
    list_display = ('type', 'device')