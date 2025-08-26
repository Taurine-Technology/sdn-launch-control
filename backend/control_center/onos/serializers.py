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
from .models import Meter, Category
from network_device.models import NetworkDevice

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name')

class MeterSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Meter
        fields = (
            'id', 'meter_id', 'meter_type', 'rate', 'switch_id',
            'categories',
        )  # Exclude optional fields

    def create(self, validated_data):
        """
        Custom create method to handle optional fields properly.
        """
        request = self.context.get("request")

        # Extract optional fields
        mac_address = self.initial_data.get("network_device_mac")
        activation_period = validated_data.pop("activation_period", None)
        start_time = validated_data.pop("start_time", None)
        end_time = validated_data.pop("end_time", None)

        # Find network device by MAC if provided
        network_device = None
        if mac_address:
            try:
                network_device = NetworkDevice.objects.get(mac_address=mac_address)
            except NetworkDevice.DoesNotExist:
                raise serializers.ValidationError({"error": "Network device not found with this MAC address."})

        # Create the Meter instance
        meter = Meter.objects.create(
            network_device=network_device,
            activation_period=activation_period,
            start_time=start_time,
            end_time=end_time,
            **validated_data
        )

        return meter

    def to_representation(self, instance):
        """
        Customize the serialized output of a Meter instance.
        """
        data = super().to_representation(instance)

        # Add optional fields to the response
        data["network_device_mac"] = instance.network_device.mac_address if instance.network_device else None
        data["activation_period"] = instance.activation_period
        data["start_time"] = instance.start_time.strftime("%H:%M") if instance.start_time else None
        data["end_time"] = instance.end_time.strftime("%H:%M") if instance.end_time else None

        return data
