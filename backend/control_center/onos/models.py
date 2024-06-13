from django.core.exceptions import ValidationError
from django.db import models
from general.models import Device


# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Meter(models.Model):
    METER_TYPES = (('drop', 'drop'),)
    controller_device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='meters')
    meter_id = models.IntegerField(unique=True)
    meter_type = models.CharField(max_length=30, choices=METER_TYPES)
    rate = models.IntegerField()
    switch_id = models.CharField(max_length=30)
    categories = models.ManyToManyField(Category, blank=True)


class OnosOpenFlowDevice(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='openflow_device')
    openflow_id = models.CharField(max_length=30)
