from rest_framework import serializers
from .models import Device, Bridge, Port


class PortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Port
        fields = ['name', ]


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['name', 'device_type', 'os_type', 'lan_ip_address', 'num_ports', 'ovs_enabled', 'ovs_version',
                  'openflow_version']


class BridgeSerializer(serializers.ModelSerializer):
    device = DeviceSerializer(read_only=True)
    ports = PortSerializer(many=True, read_only=True)

    class Meta:
        model = Bridge
        fields = ['name', 'dpid', 'device', 'ports']
