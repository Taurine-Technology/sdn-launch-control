from django.contrib import admin

# Register your models here.
from .models import Device


@admin.register(Device)
class NetworkDeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'lan_ip_address', 'device_type', 'os_type',  'ovs_enabled')
