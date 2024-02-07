from rest_framework import serializers
from .models import Controller


class ControllerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Controller
        fields = '__all__'
