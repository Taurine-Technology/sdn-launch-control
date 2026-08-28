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

from rest_framework import serializers
from .models import SNMPDevice, SNMPMetrics, SNMPInterfaceStats


class SNMPDeviceSerializer(serializers.ModelSerializer):
    """
    Serializer for SNMPDevice model.
    Used for creating, updating, and listing SNMP devices.
    """
    vendor_display = serializers.CharField(source='get_vendor_display', read_only=True)

    class Meta:
        model = SNMPDevice
        fields = (
            'id',
            'network_device',
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
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'last_successful_poll',
            'last_poll_attempt',
            'consecutive_failures',
            'created_at',
            'updated_at',
        )


class SNMPMetricsSerializer(serializers.ModelSerializer):
    """
    Serializer for SNMPMetrics model.
    Read-only serializer for querying historical metrics.
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
    Read-only serializer for querying historical interface statistics.
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