from django.contrib import admin
from .models import NetworkDevice

@admin.register(NetworkDevice)
class NetworkDeviceAdmin(admin.ModelAdmin):
    list_display = ('account', 'mac_address', 'device_type', 'verified')