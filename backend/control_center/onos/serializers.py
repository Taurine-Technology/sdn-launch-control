from rest_framework import serializers
from .models import Meter, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name')

class MeterSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Meter
        fields = ('id', 'meter_id', 'meter_type', 'rate', 'switch_id', 'categories')
