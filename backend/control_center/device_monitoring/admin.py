"""
Django admin configuration for device_monitoring app
"""
from django.contrib import admin
from .models import DeviceStats, DeviceHealthAlert


@admin.register(DeviceStats)
class DeviceStatsAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'cpu', 'memory', 'disk', 'timestamp')
    list_filter = ('ip_address', 'timestamp')
    search_fields = ('ip_address',)
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'


@admin.register(DeviceHealthAlert)
class DeviceHealthAlertAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'last_cpu_alert', 'last_memory_alert', 'last_disk_alert')
    search_fields = ('ip_address',)
    readonly_fields = ('last_cpu_alert', 'last_memory_alert', 'last_disk_alert')

