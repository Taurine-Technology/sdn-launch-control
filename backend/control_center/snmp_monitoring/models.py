# File: models.py
# Copyright (C) 2025 Taurine Technology
#
# This file is part of the SDN Launch Control project.
#
# This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0),
# available at: https://www.gnu.org/licenses/agpl-3.0.en.html#license-text
#
# Contributions to this project are governed by a Contributor License Agreement (CLA).
# By submitting a contribution, contributors grant Taurine Technology exclusive rights to
# the contribution, including the right to relicense it under a different license
# at the copyright owner's discretion.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under this license is provided "AS IS", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the GNU Affero General Public License for more details.
#
# For inquiries, contact Keegan White at keeganwhite@taurinetech.com.

from django.db import models
from network_device.models import NetworkDevice

# Vendor choices for SNMP devices
VENDOR_CHOICES = (
    ('mikrotik', 'MikroTik'),
    ('ubiquiti', 'Ubiquiti'),
    ('tp_link', 'TP-Link'),
    ('cisco', 'Cisco'),
    ('netgear', 'Netgear'),
    ('d_link', 'D-Link'),
    ('huawei', 'Huawei'),
    ('hp', 'HP'),
    ('other', 'Other'),
)


class SNMPDevice(models.Model):
    """
    Model for storing SNMP device configuration.

    Links to NetworkDevice (optional) and stores SNMP-specific configuration
    including community string, vendor, and polling settings.
    """
    # Optional link to existing NetworkDevice
    network_device = models.ForeignKey(
        NetworkDevice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='snmp_devices',
        help_text="Optional link to existing network device"
    )

    # Device identification
    name = models.CharField(
        max_length=100,
        help_text="Human-readable device name"
    )
    ip_address = models.GenericIPAddressField(
        db_index=True,
        help_text="IP address of the SNMP device"
    )
    vendor = models.CharField(
        max_length=50,
        choices=VENDOR_CHOICES,
        default='other',
        db_index=True,
        help_text="Device vendor/manufacturer"
    )

    # SNMP v2c configuration
    community_string = models.CharField(
        max_length=100,
        help_text="SNMP community string (typically 'public' or 'private')"
    )
    snmp_version = models.CharField(
        max_length=10,
        default='2c',
        choices=[('2c', 'SNMP v2c')],
        help_text="SNMP version (v3 support to be added later)"
    )
    port = models.IntegerField(
        default=161,
        help_text="SNMP port (default: 161)"
    )

    # Polling configuration
    polling_interval = models.IntegerField(
        default=60,
        help_text="Polling interval in seconds (default: 60)"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this device should be polled"
    )

    # Status tracking
    last_successful_poll = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last successful SNMP poll"
    )
    last_poll_attempt = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last poll attempt (successful or not)"
    )
    consecutive_failures = models.IntegerField(
        default=0,
        help_text="Number of consecutive polling failures"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['vendor']),
            models.Index(fields=['is_active']),
        ]
        unique_together = [('ip_address', 'port')]  # This might change when we add cloud support

    def __str__(self):
        return f"{self.name} ({self.ip_address}) - {self.get_vendor_display()}"


class SNMPMetrics(models.Model):
    """
    Time-series model for storing SNMP device metrics.
    Optimized for TimescaleDB hypertable storage.

    Stores general device metrics like CPU, memory, uptime, etc.
    """
    device = models.ForeignKey(
        SNMPDevice,
        on_delete=models.CASCADE,
        related_name='metrics',
        db_index=True,
        help_text="SNMP device this metric belongs to"
    )

    # Metric values
    cpu_usage = models.FloatField(
        null=True,
        blank=True,
        help_text="CPU usage percentage"
    )
    memory_usage = models.FloatField(
        null=True,
        blank=True,
        help_text="Memory usage percentage"
    )
    disk_usage = models.FloatField(
        null=True,
        blank=True,
        help_text="Disk usage percentage"
    )
    uptime_seconds = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Device uptime in seconds"
    )

    # Additional metrics (stored as JSON or separate fields as needed)
    # For now, we'll keep it simple with common metrics

    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when metric was collected"
    )

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"Metrics for {self.device.name} @ {self.timestamp}"


class SNMPInterfaceStats(models.Model):
    """
    Time-series model for storing SNMP interface statistics.
    Optimized for TimescaleDB hypertable storage.

    Stores per-interface statistics similar to PortUtilizationStats.
    """
    device = models.ForeignKey(
        SNMPDevice,
        on_delete=models.CASCADE,
        related_name='interface_stats',
        db_index=True,
        help_text="SNMP device this interface belongs to"
    )

    interface_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Interface name (e.g., 'eth0', 'wlan0')"
    )
    interface_index = models.IntegerField(
        null=True,
        blank=True,
        help_text="SNMP interface index (ifIndex)"
    )

    # Interface statistics
    bytes_in = models.BigIntegerField(
        default=0,
        help_text="Total bytes received on interface"
    )
    bytes_out = models.BigIntegerField(
        default=0,
        help_text="Total bytes transmitted on interface"
    )
    packets_in = models.BigIntegerField(
        default=0,
        help_text="Total packets received on interface"
    )
    packets_out = models.BigIntegerField(
        default=0,
        help_text="Total packets transmitted on interface"
    )
    errors_in = models.BigIntegerField(
        default=0,
        help_text="Input errors on interface"
    )
    errors_out = models.BigIntegerField(
        default=0,
        help_text="Output errors on interface"
    )

    # Calculated fields (similar to PortUtilizationStats)
    throughput_mbps = models.FloatField(
        null=True,
        blank=True,
        help_text="Calculated throughput in Mbps (if available)"
    )
    utilization_percent = models.FloatField(
        null=True,
        blank=True,
        help_text="Interface utilization percentage (if link speed known)"
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when statistics were collected"
    )

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', 'interface_name', 'timestamp']),
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"Interface {self.interface_name} on {self.device.name} @ {self.timestamp}"


class SNMPDeviceAlert(models.Model):
    """
    Tracks last notification time per device to prevent notification flooding.
    Similar to DeviceHealthAlert in device_monitoring app.
    """
    device = models.OneToOneField(
        SNMPDevice,
        on_delete=models.CASCADE,
        related_name='alert_settings',
        help_text="SNMP device for alert tracking"
    )
    last_cpu_alert = models.DateTimeField(null=True, blank=True)
    last_memory_alert = models.DateTimeField(null=True, blank=True)
    last_disk_alert = models.DateTimeField(null=True, blank=True)
    last_interface_alert = models.DateTimeField(null=True, blank=True)
    last_connection_failure_alert = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Alert settings for {self.device.name}"