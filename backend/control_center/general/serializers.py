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
from .models import Device, Bridge, Port
from .models import Controller


class ControllerSerializer(serializers.ModelSerializer):
    lan_ip_address = serializers.SerializerMethodField()

    class Meta:
        model = Controller
        fields = ['id', 'type', 'port_num', 'lan_ip_address']

    def get_lan_ip_address(self, obj):
        # Here, obj is a Controller instance
        # Return the lan_ip_address of the associated Device
        return obj.device.lan_ip_address if obj.device else None


class PortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Port
        fields = ['id', 'name', 'ovs_port_number', 'link_speed', 'is_up']


class PortUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating port link_speed only.
    All other fields are read-only.
    """

    class Meta:
        model = Port
        fields = ['id', 'name', 'ovs_port_number', 'link_speed', 'is_up']
        read_only_fields = ['id', 'name', 'ovs_port_number', 'is_up']

    def save(self, **kwargs):
        # Only save link_speed, filter validated_data to just link_speed
        if 'link_speed' in self.validated_data:
            # Filter validated_data to only include link_speed
            filtered_data = {'link_speed': self.validated_data['link_speed']}
            # Temporarily store original validated_data
            original_validated_data = self.validated_data
            # Replace with filtered data
            self._validated_data = filtered_data
            try:
                instance = super().save(**kwargs)
                # Ensure only link_speed was updated in the database
                instance.save(update_fields=['link_speed'])
                return instance
            finally:
                # Restore original validated_data
                self._validated_data = original_validated_data
        return super().save(**kwargs)


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = [
            'id',
            'name',
            'device_type',
            'os_type',
            'lan_ip_address',
            'num_ports',
            'ovs_enabled',
            'ovs_version',
            'openflow_version',
            'api_url'
        ]



class BridgeSerializer(serializers.ModelSerializer):
    device = DeviceSerializer(read_only=True)
    ports = PortSerializer(many=True, read_only=True)
    controller = ControllerSerializer(read_only=True)

    class Meta:
        model = Bridge
        fields = ['id', 'name', 'dpid', 'odl_node_id', 'device', 'ports', 'controller', 'api_url']

