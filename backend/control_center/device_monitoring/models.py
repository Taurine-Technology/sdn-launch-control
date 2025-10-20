# File: models.py
# Copyright (C) 2025 Taurine Technology
#
# This file is part of the SDN Launch Control project.
#
# This project is licensed under the GNU General Public License v3.0 (GPL-3.0),
# available at: https://www.gnu.org/licenses/gpl-3.0.en.html#license-text
#
# Contributions to this project are governed by a Contributor License Agreement (CLA).
# By submitting a contribution, contributors grant Taurine Technology exclusive rights to
# the contribution, including the right to relicense it under a different license
# at the copyright owner's discretion.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under this license is provided "AS IS", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the GNU General Public License for more details.
#
# For inquiries, contact Keegan White at keeganwhite@taurinetech.com.

from django.db import models


class DeviceStats(models.Model):
    """
    Time-series model for storing device system statistics.
    Optimized for TimescaleDB hypertable storage.
    """
    ip_address = models.GenericIPAddressField(db_index=True)
    cpu = models.FloatField(help_text="CPU usage percentage")
    memory = models.FloatField(help_text="Memory usage percentage")
    disk = models.FloatField(help_text="Disk usage percentage")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"Stats for {self.ip_address} @ {self.timestamp}"


class DeviceHealthAlert(models.Model):
    """
    Tracks last notification time per device to prevent notification flooding.
    """
    ip_address = models.GenericIPAddressField(unique=True)
    last_cpu_alert = models.DateTimeField(null=True, blank=True)
    last_memory_alert = models.DateTimeField(null=True, blank=True)
    last_disk_alert = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Health alerts for {self.ip_address}"


class PortUtilizationStats(models.Model):
    """
    Time-series model for storing port utilization statistics.
    Optimized for TimescaleDB hypertable storage with compression and retention.
    
    Stores throughput and utilization data from OpenFlow port monitoring.Data is compressed after 6 hours.
    Retention policy automatically removes data older than 90 days.
    """
    ip_address = models.GenericIPAddressField(db_index=True, help_text="IP address of the device")
    port_name = models.CharField(max_length=100, db_index=True, help_text="Name of the port/interface")
    throughput_mbps = models.FloatField(help_text="Calculated throughput in Mbps")
    utilization_percent = models.FloatField(null=True, blank=True, help_text="Percentage of link capacity used (NULL if link_speed unknown)")
    rx_bytes_diff = models.BigIntegerField(help_text="Received bytes delta from previous measurement")
    tx_bytes_diff = models.BigIntegerField(help_text="Transmitted bytes delta from previous measurement")
    duration_diff = models.FloatField(help_text="Time period for the measurement in seconds")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['ip_address', 'port_name', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"Port {self.port_name} on {self.ip_address}: {self.utilization_percent:.2f}% utilized @ {self.timestamp}"


class PortUtilizationAlert(models.Model):
    """
    Tracks last notification time per port to prevent notification flooding.
    """
    ip_address = models.GenericIPAddressField(db_index=True)
    port_name = models.CharField(max_length=100, db_index=True)
    last_utilization_alert = models.DateTimeField(null=True, blank=True)
    last_null_link_speed_alert = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [('ip_address', 'port_name')]

    def __str__(self):
        return f"Port utilization alerts for {self.port_name} on {self.ip_address}"
