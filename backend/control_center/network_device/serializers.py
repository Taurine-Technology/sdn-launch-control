# serializers.py
from rest_framework import serializers
from .models import NetworkDevice

class NetworkDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkDevice
        fields = '__all__'
