from rest_framework import serializers
from .models import Device, Bridge, Port
from .models import Controller


class ControllerSerializer(serializers.ModelSerializer):
    lan_ip_address = serializers.SerializerMethodField()

    class Meta:
        model = Controller
        fields = ['type', 'port_num', 'lan_ip_address']  # Include other fields as needed

    def get_lan_ip_address(self, obj):
        # Here, obj is a Controller instance
        # Return the lan_ip_address of the associated Device
        return obj.device.lan_ip_address if obj.device else None


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
    controller = ControllerSerializer(read_only=True)  # Make sure this is included

    class Meta:
        model = Bridge
        fields = ['name', 'dpid', 'device', 'ports', 'controller']

