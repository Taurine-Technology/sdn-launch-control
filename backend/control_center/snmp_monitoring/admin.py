# File: admin.py
# Copyright (C) 2025 Taurine Technology
#
# This file is part of the SDN Launch Control project.
#
# This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0),
# available at: https://www.gnu.org/licenses/agpl-3.0.en.html#license-text

from django.contrib import admin
from .models import SNMPDevice, SNMPMetrics, SNMPInterfaceStats, SNMPDeviceAlert


@admin.register(SNMPDevice)
class SNMPDeviceAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'ip_address', 'vendor', 'is_active',
        'last_successful_poll', 'consecutive_failures'
    )
    list_filter = ('vendor', 'is_active')
    search_fields = ('name', 'ip_address')
    readonly_fields = ('last_successful_poll', 'last_poll_attempt', 'consecutive_failures', 'created_at', 'updated_at')


@admin.register(SNMPMetrics)
class SNMPMetricsAdmin(admin.ModelAdmin):
    list_display = ('device', 'cpu_usage', 'memory_usage', 'disk_usage', 'uptime_seconds', 'timestamp')
    list_filter = ('device',)
    date_hierarchy = 'timestamp'


@admin.register(SNMPInterfaceStats)
class SNMPInterfaceStatsAdmin(admin.ModelAdmin):
    list_display = ('device', 'interface_name', 'bytes_in', 'bytes_out', 'timestamp')
    list_filter = ('device', 'interface_name')
    date_hierarchy = 'timestamp'


@admin.register(SNMPDeviceAlert)
class SNMPDeviceAlertAdmin(admin.ModelAdmin):
    list_display = ('device', 'last_cpu_alert', 'last_memory_alert', 'last_connection_failure_alert')
    list_filter = ('device',)
