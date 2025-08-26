from rest_framework import serializers
from .models import Plugin, PluginRequirement, PluginInstallation, SnifferInstallationConfig
from general.models import Device
from general.serializers import DeviceSerializer


class PluginSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plugin
        fields = '__all__'

class PluginRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = PluginRequirement
        fields = '__all__'


class SnifferInstallationConfigSerializer(serializers.ModelSerializer):

    # Allow specifying the installation ID when creating/updating config
    installation_id = serializers.PrimaryKeyRelatedField(
        queryset=PluginInstallation.objects.all(),
        source='installation', # Link to the 'installation' field on the model
        write_only=True,
        required=True  # default, but will be set to False on update
    )

    class Meta:
        model = SnifferInstallationConfig
        fields = [
            'installation_id', # Use this for writing
            # 'installation', # Use this if you want nested read data
            'api_base_url',
            'monitor_interface',
            'port_to_client',
            'port_to_router',
            'bridge_name',
        ]
        # If 'installation' is included above for reading, make it read-only:
        # read_only_fields = ('installation',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If updating (instance exists), don't require installation_id
        if self.instance is not None:
            self.fields['installation_id'].required = False

    #  ensure the installation_id corresponds to the correct plugin type before saving.
    def validate_installation_id(self, value):
        # 'value' here is the PluginInstallation instance
        if value.plugin.name != 'tau-traffic-classification-sniffer':
             raise serializers.ValidationError("Configuration can only be linked to a sniffer plugin installation.")
        return value


class PluginInstallationSerializer(serializers.ModelSerializer):
    plugin = PluginSerializer(read_only=True)
    device = DeviceSerializer(read_only=True)
    # Add the nested sniffer config (will be null if not a sniffer install)
    sniffer_config = SnifferInstallationConfigSerializer(read_only=True, required=False)

    plugin_id = serializers.PrimaryKeyRelatedField(
        queryset=Plugin.objects.all(), source='plugin', write_only=True
    )
    device_id = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(), source='device', required=False, allow_null=True, write_only=True
    )

    class Meta:
        model = PluginInstallation
        fields = [
            'id',
            'plugin',
            'device',
            'installed_at',
            'sniffer_config', # Include the nested config here
            'plugin_id',
            'device_id',
        ]
        read_only_fields = ('installed_at', 'plugin', 'device', 'sniffer_config')


