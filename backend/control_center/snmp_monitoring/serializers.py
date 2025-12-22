# File: serializers.py
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

"""
Serializers for SNMP monitoring API endpoints.

Provides serializers for:
- SNMPDevice: Full CRUD operations for SNMP device configuration
- SNMPMetrics: Read-only access to device-level metrics
- SNMPInterfaceStats: Read-only access to interface statistics
"""

from rest_framework import serializers
from .models import SNMPDevice, SNMPMetrics, SNMPInterfaceStats, SNMPDeviceAlert


class SNMPDeviceSerializer(serializers.ModelSerializer):
    """
    Serializer for SNMPDevice model.
    
    Provides full CRUD operations for SNMP device configuration.
    Sensitive fields like community_string are write-only for security.
    """
    # Make community_string write-only for security
    community_string = serializers.CharField(
        write_only=True,
        required=True,
        help_text="SNMP community string (write-only for security)"
    )
    
    # Read-only computed fields
    vendor_display = serializers.CharField(
        source='get_vendor_display',
        read_only=True,
        help_text="Human-readable vendor name"
    )
    
    # Status fields (read-only)
    is_healthy = serializers.SerializerMethodField(
        help_text="True if device has been successfully polled recently"
    )
    
    class Meta:
        model = SNMPDevice
        fields = (
            'id',
            'name',
            'ip_address',
            'vendor',
            'vendor_display',
            'community_string',
            'snmp_version',
            'port',
            'polling_interval',
            'is_active',
            'last_successful_poll',
            'last_poll_attempt',
            'consecutive_failures',
            'is_healthy',
            'network_device',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'vendor_display',
            'last_successful_poll',
            'last_poll_attempt',
            'consecutive_failures',
            'is_healthy',
            'created_at',
            'updated_at',
        )
    
    def get_is_healthy(self, obj):
        """
        Determine if device is healthy based on polling status.
        
        A device is considered healthy if:
        - It has been successfully polled at least once
        - It has fewer than 3 consecutive failures
        """
        if obj.last_successful_poll is None:
            return False
        return obj.consecutive_failures < 3
    
    def validate_port(self, value):
        """Validate SNMP port is in valid range."""
        if value < 1 or value > 65535:
            raise serializers.ValidationError("Port must be between 1 and 65535")
        return value
    
    def validate_polling_interval(self, value):
        """Validate polling interval is reasonable."""
        if value < 10:
            raise serializers.ValidationError("Polling interval must be at least 10 seconds")
        if value > 86400:
            raise serializers.ValidationError("Polling interval cannot exceed 24 hours (86400 seconds)")
        return value


class SNMPDeviceListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for SNMPDevice list views.
    
    Excludes sensitive and detailed fields for better performance in list views.
    """
    vendor_display = serializers.CharField(source='get_vendor_display', read_only=True)
    is_healthy = serializers.SerializerMethodField()
    
    class Meta:
        model = SNMPDevice
        fields = (
            'id',
            'name',
            'ip_address',
            'vendor',
            'vendor_display',
            'is_active',
            'is_healthy',
            'last_successful_poll',
            'consecutive_failures',
        )
    
    def get_is_healthy(self, obj):
        if obj.last_successful_poll is None:
            return False
        return obj.consecutive_failures < 3


class SNMPMetricsSerializer(serializers.ModelSerializer):
    """
    Serializer for SNMPMetrics model.
    
    Read-only serializer for querying device-level metrics (CPU, memory, uptime).
    """
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_ip = serializers.CharField(source='device.ip_address', read_only=True)
    
    class Meta:
        model = SNMPMetrics
        fields = (
            'id',
            'device',
            'device_name',
            'device_ip',
            'cpu_usage',
            'memory_usage',
            'disk_usage',
            'uptime_seconds',
            'timestamp',
        )
        read_only_fields = fields


class SNMPInterfaceStatsSerializer(serializers.ModelSerializer):
    """
    Serializer for SNMPInterfaceStats model.
    
    Read-only serializer for querying per-interface statistics.
    """
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_ip = serializers.CharField(source='device.ip_address', read_only=True)
    
    class Meta:
        model = SNMPInterfaceStats
        fields = (
            'id',
            'device',
            'device_name',
            'device_ip',
            'interface_name',
            'interface_index',
            'bytes_in',
            'bytes_out',
            'packets_in',
            'packets_out',
            'errors_in',
            'errors_out',
            'throughput_mbps',
            'utilization_percent',
            'timestamp',
        )
        read_only_fields = fields


class SNMPDeviceAlertSerializer(serializers.ModelSerializer):
    """
    Serializer for SNMPDeviceAlert model.

    Read-only serializer for viewing alert timestamps.
    """
    device_name = serializers.CharField(source='device.name', read_only=True)

    class Meta:
        model = SNMPDeviceAlert
        fields = (
            'id',
            'device',
            'device_name',
            'last_cpu_alert',
            'last_memory_alert',
            'last_disk_alert',
            'last_interface_alert',
            'last_connection_failure_alert',
        )
        read_only_fields = fields

