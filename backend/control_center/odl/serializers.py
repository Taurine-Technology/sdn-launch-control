# File: odl/serializers.py
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
from .models import OdlMeter
from .models import Category
from general.models import Bridge

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name',)

class OdlMeterSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    controller_ip = serializers.CharField(source='controller_device.lan_ip_address', read_only=True)
    network_device_mac = serializers.CharField(source='network_device.mac_address', read_only=True, allow_null=True)
    class Meta:
        model = OdlMeter
        fields = (
            'id',
            'controller_ip',
            'meter_id_on_odl',
            'switch_node_id',
            'rate',
            'meter_type',
            'activation_period',
            'network_device_mac',
            'start_time',
            'end_time',
            'categories',
            'meter_id_on_odl', #(covered by meter_id for read)
            'switch_node_id', #(covered by switch_id for read)
            'controller_device', #(handled by controller_ip for read, view handles write)
            'network_device' #(handled by network_device_mac for read, view handles write)
        )

class OdlNodeSerializer(serializers.ModelSerializer):
    """
    Serializer for representing ODL-controlled nodes (Bridges).
    """
    # The 'id' here will be the Bridge's database PK.
    # 'odl_node_id' is the crucial field for ODL.
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_ip = serializers.CharField(source='device.lan_ip_address', read_only=True)
    bridge_name = serializers.CharField(source='name', read_only=True)

    class Meta:
        model = Bridge
        fields = (
            'id', # Bridge DB PK
            'odl_node_id',
            'bridge_name', # Bridge name
            'dpid',
            'device_name', # Name of the device hosting the bridge
            'device_ip',   # IP of the device hosting the bridge
        )