# File: serializers.py
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

from rest_framework import serializers
from .models import (
    PortUtilizationStats,
    DevicePingStats,
    DeviceStats,
)


class PortUtilizationStatsSerializer(serializers.ModelSerializer):
    """
    Serializer for PortUtilizationStats model.
    
    Read-only serializer for querying historical port utilization data.
    Provides all fields including throughput, utilization percentage, and timing data.
    """
    
    class Meta:
        model = PortUtilizationStats
        fields = (
            'id',
            'ip_address',
            'port_name',
            'throughput_mbps',
            'utilization_percent',
            'rx_bytes_diff',
            'tx_bytes_diff',
            'duration_diff',
            'timestamp',
        )
        read_only_fields = fields


class DevicePingStatsSerializer(serializers.ModelSerializer):
    """
    Serializer for DevicePingStats model.
    Returns ping check results for monitored network devices.
    """
    class Meta:
        model = DevicePingStats
        fields = (
            'id',
            'device',
            'is_alive',
            'successful_pings',
            'timestamp',
        )
        read_only_fields = fields


class DeviceStatsSerializer(serializers.ModelSerializer):
    """
    Serializer for DeviceStats model. Useful for parity and potential raw listings.
    """
    class Meta:
        model = DeviceStats
        fields = (
            'id',
            'ip_address',
            'cpu',
            'memory',
            'disk',
            'timestamp',
        )
        read_only_fields = fields
